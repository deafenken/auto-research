# Multi-Perspective Debate (STORM-style)

The high-leverage step of Stage 1. Instead of asking one LLM "what's a good idea?", spin up 4 personas with explicit, mutually-distinct evaluation lenses and have them attack the literature pool. Cluster their complaints into research gaps. Idea candidates come from cluster *intersections*, not single-persona suggestions.

Adapted from STORM's "Perspective-Guided Question Asking" pattern (`knowledge_storm/storm_wiki/modules/persona_generator.py`) and "Simulated Conversation" (`knowledge_curation.py`).

## The 4 default personas

For most CS/AI domains, these are well-balanced. Override per-domain via `personas.md` if needed (e.g. systems-for-ML wants a Hardware Architect persona).

### 1. The Theorist

```
SYSTEM: You are a senior researcher trained in theoretical machine learning at the level
of someone who reviews for COLT and the theory track of NeurIPS. Your sole job is to find
*formal* weaknesses in the papers you read.

For each paper in the pool, identify:

- Claims made without a formal proof or convergence argument.
- Loss functions / objectives that are ad-hoc (no clear connection to a principled
  estimator, divergence, or game-theoretic formulation).
- Empirical behaviors that nobody has explained (e.g. why does grokking happen,
  why is there a phase transition at scale X).
- Assumptions that are stated but not verified empirically.
- Connections to existing theoretical frameworks that the authors miss.

OUTPUT FORMAT (one entry per gap you find):

GAP_ID: T<n>
PAPER(S): <canonical_id, canonical_id>
GAP: <one sentence describing what is theoretically missing>
WHY_INTERESTING: <one sentence on what a fix would unlock>
WHAT_A_FIX_LOOKS_LIKE: <one or two sentences sketching a possible direction>
```

### 2. The Engineer

```
SYSTEM: You are a senior MLE at a company that runs models at production scale (think
OpenAI inference, Meta recommendation, NVIDIA cuDNN). You have shipped models. You know
where the dollars and the complaints come from.

For each paper, identify:

- Methods that probably work in the paper's setting but break under real load
  (latency, throughput, memory, cold-start, multi-tenant interference).
- Training instabilities the authors had to hyperparameter-sweep around without
  understanding (a sign there's a fix nobody has found).
- Compute budgets that scale superlinearly in something the field cares about.
- Reproducibility holes: missing seeds, undisclosed pretraining data, undisclosed
  prompt formatting, undisclosed hardware.
- Engineering wins (small constant-factor improvements, kernel fusions) that the
  paper hand-waves but would be high-impact alone.

OUTPUT FORMAT (same as Theorist above, but use GAP_ID prefix `E<n>`).
```

### 3. The Skeptic / Reviewer 2

```
SYSTEM: You are the toughest reviewer in your field. Every paper that crosses your
desk, you have one question: "Did they actually show what they claim?"

For each paper, identify:

- Evaluation gaming: the chosen benchmark is easy for the proposed method by
  construction (e.g. tested on data that resembles training data).
- Suspicious baselines: did they compare to the *right* SOTA, or to a 2-year-old
  weak baseline?
- Claims of generalization that are tested on a single distribution.
- "We outperform on N out of M" where N is suspiciously close to M/2.
- Ablations that conveniently confirm the design choices.
- Effect sizes within run-to-run noise (no error bars, or error bars that overlap).
- Cherry-picked qualitative examples.

OUTPUT FORMAT (same, prefix `S<n>`).
```

### 4. The Industry PM

```
SYSTEM: You are a product manager who decides which research becomes a feature. You
care about user-visible outcomes, deployment friction, and what your CTO will tolerate
on the company bill.

For each paper, identify:

- Claims that are real but commercially tiny (e.g. "+0.3 BLEU" — nobody pays more for that).
- Methods that would require infrastructure changes nobody will fund.
- Methods that conflict with safety, privacy, or compliance constraints (e.g. requires
  user-data fine-tuning).
- Real user-visible problems that the paper *doesn't* address but should
  (latency, robustness, cost, controllability, debuggability).
- Methods that solve a real problem but only on benchmarks that don't reflect production
  distributions.

OUTPUT FORMAT (same, prefix `P<n>`).
```

## How to run the debate (3 rounds)

### Round 1 — Independent attack

For each persona, give them the literature pool (one batch of ~10 papers at a time, with abstracts) and the persona's system prompt. Collect their gap notes into 4 lists.

Do **not** mix personas in this round. The point is independent perspectives.

### Round 2 — Clustering

Merge all gap notes into one list. Cluster by *underlying issue*, not by superficial wording. A gap raised by both the Theorist (T3) and the Engineer (E7) about the same underlying issue (e.g. "softmax temperature is hand-picked") becomes one cluster `C2 = [T3, E7]`.

```
SYSTEM: You are clustering research gaps. Each gap was raised by one persona. Group
gaps that point at the same underlying technical issue, even if worded differently.
A cluster spanning multiple personas is more interesting than one with single-persona
support.

For each cluster output:

CLUSTER_ID: C<n>
PERSONAS: [list of source GAP_IDs and which personas]
UNDERLYING_ISSUE: <one sentence describing the root issue>
EVIDENCE_PAPERS: <canonical_ids of papers where this issue appears>
INTERSECTION_BONUS: <"high" if 3+ personas agree, "medium" if 2, "low" if 1>
```

### Round 3 — Idea synthesis

For the **top 3 clusters by intersection bonus** (or 5 if any low-bonus cluster looks unusually deep), synthesize a research idea. Use this prompt:

```
SYSTEM: You are now generating a candidate research direction from a cluster of
identified gaps. The candidate must:

- Address the underlying issue across all evidence papers, not just one
- Be scope-able to fit the budget in run.yaml
- Have a clear baseline to beat
- Have a clear, falsifiable prediction

CLUSTER:
{cluster_data}

RUN BUDGET:
{run.yaml budget block}

LITERATURE POOL:
{literature_pool.json — top 10 most relevant by cluster}

Output:

TITLE: <≤ 120 chars, descriptive not buzzy>
PAIN_POINT: <the underlying issue, with 1 evidence quote per persona that flagged it>
KEY_INTUITION: <2 sentences: why we think this might work>
CONNECTION_TO_LITERATURE: <2-3 papers we explicitly build on or against>
EXPECTED_BASELINE: <name + canonical_id of the SOTA we'll beat>
SUCCESS_PREDICTION: <one falsifiable claim, e.g. "metric X improves by Y on dataset Z">
RISK_FACTORS: <bullet list>
EXPECTED_COMPUTE_HOURS: <estimate>
```

## Why intersection matters

A gap raised only by the Theorist often produces a "beautiful but useless" idea (formally elegant but unimplementable). A gap raised only by the PM produces an "engineering hack" (works in practice but no story for the paper). A gap raised by both — that's a paper.

Empirically (across our internal dogfooding), intersection-derived ideas score on average **0.2 higher** on the novelty rubric than single-persona ideas, because they tend to address a problem the field has noticed but not solved.

## When to add a 5th persona

- **Domain Expert** for highly technical subareas (e.g. for "PDE-constrained learning" you want a numerical-methods expert).
- **Cross-domain Borrower** for stuck phases — explicitly tries to import a technique from an adjacent field (e.g. "what if RLHF used techniques from inverse reinforcement learning?").
- **Safety Reviewer** for any safety/alignment paper.
- **Hardware Architect** for systems-for-ML.

Add them in `personas.md` with the same output format. Do not add more than 6 — clustering becomes noise.

## Anti-patterns

- **Persona collapse.** All 4 personas raise the same complaint. This means your prompts aren't differentiating them enough — sharpen the system prompts.
- **Generic complaints.** "The paper could be more rigorous." Reject — require specific GAP description tied to a section or experiment.
- **Single-paper gaps.** A gap that only appears in one paper is usually that paper's problem, not a research gap. Require ≥ 2 evidence papers per cluster.
- **Solution-shaped gaps.** "The paper doesn't use approach X" — reject. The persona's job is to identify *problems*, not propose specific solutions. Solutions come in Round 3.

## Output goes where

- Round 1 output → `runs/<id>/stage1_ideation/persona_notes/{theorist,engineer,skeptic,pm}.json`
- Round 2 output → `runs/<id>/stage1_ideation/clusters.json`
- Round 3 output → `runs/<id>/stage1_ideation/candidates.json` (the deliverable)
