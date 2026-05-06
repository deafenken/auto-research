# Literature Search Protocols

How Stage 1 collects the paper pool that everything else hangs off of. This is the *only* legitimate source of citations — anything not in `literature_pool.json` cannot appear in the final paper (see integrity rule 2).

## Three sources, one priority order

| Priority | Source | Best for | API |
|---|---|---|---|
| 1 | Semantic Scholar | High-citation papers, citation graph traversal | `api.semanticscholar.org/graph/v1` |
| 2 | arXiv | Recent (last 6 months), preprints not yet on S2 | `export.arxiv.org/api/query` |
| 3 | OpenReview | ICLR open reviews — gold for gap mining | `api2.openreview.net` |

Always start with Semantic Scholar (best metadata). Fall back to arXiv if rate-limited (S2 gives ~100 req/5min unauthenticated). Use OpenReview as a *separate* pass for the gap-mining step, not as a general search.

## Query construction

The naive query "LLM hallucination" returns 50k results. Always combine:

```
domain_kw  AND  (recent OR high_impact OR specific_subarea)  AND  -known_dead_end
```

Concrete templates per domain in `query-templates.md` (TODO: extend as you encounter new domains). Default keywords to layer on:

- **LLM**: `language model`, `LLM`, `transformer`, `instruction tuning`, `RLHF`, `alignment`
- **CV**: `vision`, `image`, `segmentation`, `detection`, `diffusion`, `representation learning`
- **RL**: `reinforcement learning`, `policy gradient`, `RL`, `Q-learning`, `PPO`, `model-based`
- **Multimodal**: `multimodal`, `vision-language`, `VLM`, `audio-language`, `cross-modal`

## Semantic Scholar protocol

```
GET /graph/v1/paper/search
  query=<refined query>
  year=<current_year-2>-<current_year>
  fieldsOfStudy=Computer Science
  fields=paperId,title,abstract,year,authors,venue,citationCount,
         influentialCitationCount,openAccessPdf,externalIds,tldr
  limit=50
```

Then for the top 10 by `influentialCitationCount`:
```
GET /graph/v1/paper/{paperId}/citations
  fields=paperId,title,year,citationCount
  limit=20
```

This pulls "papers that cite the influential papers" — a much better seed than naive search because it surfaces follow-up work.

**Rate limit handling.** Free tier = 100 requests / 5 min. Cache aggressively (write `runs/<id>/.cache/s2/`). On 429, exponential backoff (5s, 15s, 45s, 120s) before falling back to arXiv.

**API key.** If `SEMANTIC_SCHOLAR_API_KEY` env var is set, use it (1000 req/sec). Don't hard-fail without one — fall back gracefully.

## arXiv protocol

```
GET http://export.arxiv.org/api/query
  search_query=cat:cs.LG AND ti:<term>
  sortBy=submittedDate
  sortOrder=descending
  max_results=50
```

Categories worth knowing:
- `cs.LG` — Machine Learning (most ML)
- `cs.CL` — Computation and Language (NLP/LLM)
- `cs.CV` — Computer Vision
- `cs.AI` — Artificial Intelligence (broader)
- `cs.NE` — Neural & Evolutionary
- `stat.ML` — Statistics ML overlap
- `cs.RO` — Robotics (for embodied)
- `cs.DC` — Distributed (for systems-for-ML)

**Pagination.** arXiv hard-caps at 30k total results per query — for narrower queries this is plenty. Use `start=N` to paginate.

**Rate limit.** No hard limit, but be polite — sleep 3s between requests.

## OpenReview protocol (the gap-mining special)

ICLR has been on OpenReview since 2017. Reviewer comments are public for accepted papers. This is unique among CS conferences and *invaluable* for finding real pain points.

```
# Find recent ICLR papers in domain
GET https://api2.openreview.net/notes/search
  group=ICLR.cc/2025/Conference
  content.title=<keyword>

# For each paper, get its reviews
GET https://api2.openreview.net/notes
  forum=<paperId>
  details=replies,writable,signatures
```

Then filter `replies` where `signatures` includes "Reviewer". The text fields to mine:

- `summary_of_contributions` — what the paper claims
- `strengths_and_weaknesses` — **gold** for limitations
- `questions` — **gold** for things-not-addressed
- `limitations` — explicit author admissions

Pull sentences containing: `limitation`, `however`, `weakness`, `would be stronger if`, `fails to`, `does not address`, `doesn't generalize`, `unclear how`, `concerned that`, `surprising that no`, `missing comparison`. These are the seed material for Phase 3 (the persona debate).

Cache to `runs/<id>/.cache/openreview/`.

**Authentication.** OpenReview's public read API does not require auth for accepted-paper reviews. For decision/private content, you'd need a guest token but that's out of scope here.

## Stopping conditions for the search

Stop the search phase when **any** of:

1. The pool has 30 papers AND last 5 fetches each contributed < 2 *new* author groups (signal: you're seeing the same authors repeatedly).
2. 10 minutes wall-clock elapsed.
3. The user budget annotation in `run.yaml::constraints` includes "fast" and you've spent 3 min.
4. Queries on 3 different keyword variants all return < 5 new results (signal: domain is exhausted within current scope).

## Deduplication

A paper can appear under different IDs (arXiv version, S2 paperId, DOI). Dedupe by:

```python
def canonical_key(paper):
    if paper.get("doi"):
        return ("doi", paper["doi"].lower())
    if paper.get("arxivId"):
        return ("arxiv", paper["arxivId"].split("v")[0])
    if paper.get("paperId"):
        return ("s2", paper["paperId"])
    # Last resort: title fingerprint
    return ("title", normalize_title(paper["title"]))

def normalize_title(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
```

Always keep the entry with the most metadata.

## What goes into `literature_pool.json`

```json
{
  "fetched_at": "ISO-8601",
  "queries_run": ["query 1", "query 2", "..."],
  "papers": [
    {
      "canonical_id": "arxiv:2403.12345",
      "title": "exact title from source",
      "authors": ["Last, First M.", "..."],
      "year": 2024,
      "venue": "NeurIPS 2024" or "arXiv preprint",
      "abstract": "...",
      "citation_count": 142,
      "influential_citation_count": 18,
      "doi": "10.xxxx/yyyy" or null,
      "arxiv_id": "2403.12345" or null,
      "s2_paper_id": "abc123..." or null,
      "url": "https://...",
      "verified_via": ["semantic_scholar:200ok", "arxiv:200ok"],
      "added_in_phase": "phase2_main_search"  // or "phase2_openreview" or "phase4_recheck"
    }
  ],
  "openreview_extracts": [
    {
      "paper_id": "...",
      "negative_quotes": ["The method does not address X.", "..."]
    }
  ]
}
```

The `verified_via` field is mandatory and is what Stage 4's citation linter cross-checks before allowing `\cite{}`.

## Common search anti-patterns

- **Searching only on the title keyword.** Papers may use synonyms ("test-time adaptation" vs "test-time training" vs "TTA"). Always search ≥ 2 variants.
- **Trusting the first hit.** S2 search ranking can be quirky for niche queries. Pull 50, then re-rank by `influentialCitationCount + (citation_count / years_old)`.
- **Ignoring negative results.** A query that returns nothing might mean "no work in this gap" — that's a *signal* for novelty, not a failure.
- **Skipping the OpenReview pass to save time.** Don't. The pass is what separates a top-tier paper from an incremental one.
