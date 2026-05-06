# Citation Verification (4-Layer)

Borrowed and adapted from AutoResearchClaw's `VerifiedRegistry`. This is the only thing standing between the agent and a paper full of fake references.

Every citation must pass **all four layers** before being added to `literature_pool.json` (or, in Stage 4, before being inserted into `paper.tex`).

## Layer 1 — Identifier resolution

Pick the strongest available identifier in this order:

1. **DOI** — `https://doi.org/<doi>` must return 200 (follow redirects).
2. **arXiv ID** — `https://arxiv.org/abs/<id>` must return 200 AND the page must show a title containing ≥ 50% of the cited title's significant words.
3. **Semantic Scholar paperId** — `https://api.semanticscholar.org/graph/v1/paper/<id>` must return 200 with valid JSON.

If none of these resolve, **the citation is rejected**. Do not fall back to "well it's probably real".

```python
def layer1_resolve(candidate):
    if candidate.doi:
        if requests.head(f"https://doi.org/{candidate.doi}", allow_redirects=True).status_code == 200:
            return ("doi", candidate.doi)
    if candidate.arxiv_id:
        r = requests.get(f"https://arxiv.org/abs/{candidate.arxiv_id}", timeout=15)
        if r.status_code == 200 and title_overlap(candidate.title, parse_arxiv_title(r.text)) > 0.5:
            return ("arxiv", candidate.arxiv_id)
    if candidate.s2_id:
        r = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/{candidate.s2_id}", timeout=15)
        if r.status_code == 200:
            return ("s2", candidate.s2_id)
    return None
```

## Layer 2 — DOI / CrossRef cross-check

Even if a DOI resolves, the metadata might disagree with what the LLM produced. Hit CrossRef:

```
GET https://api.crossref.org/works/<doi>
```

Verify:

- `message.title[0]` contains ≥ 70% word overlap with claimed title.
- `message.author[0].family` matches claimed first author's last name (case-insensitive).
- `message.published.date-parts[0][0]` matches claimed year (±1).

If any mismatch → reject. The DOI exists but it's not what the LLM thinks it is — classic confabulation pattern.

**Why this matters.** LLMs can invent plausible DOIs. CrossRef is the source of truth for what a DOI actually points to.

## Layer 3 — Semantic Scholar title-author triangulation

Even with DOI/arXiv match, do a third independent check via S2's title-search:

```
GET https://api.semanticscholar.org/graph/v1/paper/search
  query=<exact title>
  limit=5
```

The top hit must have:
- ≥ 80% title overlap (after normalization)
- First author last name match
- Year match (±1)

If S2 returns 0 results for an exact-title search, that's a **strong negative signal** — the paper may not exist at all. Reject and surface to the user.

## Layer 4 — LLM relevance check (only at use-site)

Before a paper is *used* in a `\cite{}` (Stage 4), do a one-shot relevance check:

> Given this paper's abstract: `<abstract>`
> And the claim being made: `<the sentence in paper.tex containing the cite>`
> Does the cited paper actually support, contradict, or relate to this claim? Answer in one of: SUPPORTS / CONTRADICTS / RELATED / IRRELEVANT.

If `IRRELEVANT`, block the cite — the paper is real but the LLM is misusing it (another classic pattern).

## When each layer runs

| Stage | Layer 1 | Layer 2 | Layer 3 | Layer 4 |
|---|---|---|---|---|
| 1 (Ideation) — adding to pool | ✓ | ✓ | ✓ | — |
| 4 (Writing) — about to `\cite{}` | (already done) | (already done) | (already done) | ✓ |

The Stage 1 batch verification can be parallelized — the script `assets/scripts/citation_verify.py` does this concurrently with rate-limit awareness.

## Failure handling

When verification fails, **never** silently swap in a different paper. The pipeline must:

1. Mark the candidate citation as `verification_failed: <which layer>`.
2. Re-run the search that *generated* this citation — was it from the LLM's training data instead of the live API? If yes, that's a major flag and the agent's prompt scaffolding has a bug.
3. If the citation was meant to support a specific claim, surface that the claim now lacks evidence.
4. Either find a real replacement (re-run search with different keywords) or weaken the claim.

## Practical script outline

```python
# assets/scripts/citation_verify.py
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

def verify(candidate: dict) -> dict:
    """Returns the candidate with `verified_via` populated, or `verification_failed`."""
    via = []

    l1 = layer1_resolve(candidate)
    if not l1:
        return {**candidate, "verification_failed": "layer1_no_resolver"}
    via.append(f"{l1[0]}:200ok")

    if candidate.get("doi"):
        if not layer2_crossref_match(candidate):
            return {**candidate, "verification_failed": "layer2_metadata_mismatch"}
        via.append("crossref:match")

    if not layer3_s2_triangulate(candidate):
        return {**candidate, "verification_failed": "layer3_no_s2_match"}
    via.append("s2_triangulate:match")

    return {**candidate, "verified_via": via}

def verify_batch(candidates: list, max_workers: int = 8) -> list:
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(verify, candidates))
```

## What you'll see in `literature_pool.json` for a verified entry

```json
{
  "canonical_id": "arxiv:2403.12345",
  "title": "Test-Time Compute Scaling Laws for Small Language Models",
  "authors": ["Smith, J.", "Lee, K."],
  "year": 2024,
  "doi": "10.48550/arXiv.2403.12345",
  "arxiv_id": "2403.12345",
  "s2_paper_id": "abcdef123456",
  "verified_via": ["arxiv:200ok", "crossref:match", "s2_triangulate:match"]
}
```

`verified_via` must contain at least 2 entries (Layer 1 + at least one of 2/3) for the entry to be eligible for Stage 4 citation.

## What this prevents

- Made-up DOIs that look plausible (`10.1234/xyz.5678`).
- Real DOIs attached to wrong titles (LLM mismatching from memory).
- Real papers cited for claims they don't actually support (catches via Layer 4).
- Author hallucinations (the very common "Smith et al. 2023" with a fictional Smith).
- Ghost arXiv IDs (LLMs sometimes invent IDs in valid format that don't exist).
