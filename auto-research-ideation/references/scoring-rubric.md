# Scoring Rubric — Novelty, Feasibility, and Contribution Shape

Each candidate idea gets three scores. All must be defensible — write the score *and* the 2–3 sentence justification into `candidates.json`.

## Novelty score (0–1)

The question: how much of a leap does this represent versus the closest published work?

| Score | Label | What it looks like |
|---|---|---|
| 0.9–1.0 | Paradigm-adjacent | Reframes a problem in a way nobody has — e.g. proposes a new evaluation paradigm, a new training regime, a new family of architectures. Top 5% of accepted papers at top venues. |
| 0.7–0.89 | Substantive contribution | A new mechanism / loss / training setup / dataset that addresses a known gap. Solid accept territory at top venues. |
| 0.5–0.69 | Meaningful delta | Improves on SOTA in a way that requires a non-trivial idea (not just "bigger model"). Borderline accept at top venues, comfortable accept at workshop. |
| 0.3–0.49 | Incremental | "+X% on Y benchmark" via a small architectural change or hyperparameter recipe. Workshop or weak conference. |
| 0.0–0.29 | Not a contribution | Reproduces / minorly tweaks existing work. Desk-reject. |

### How to compute

For each candidate, find the **3 closest works** in `literature_pool.json` (by abstract similarity or by being the explicit baselines/inspiration). Then:

```
1. List what they do.
2. List what the candidate does *differently*.
3. Decide which row of the table above the difference fits.
4. If you can't tell whether something existed already → search more (often this means
   the difference is smaller than you think).
```

### Anti-cheat checks

These force the score down regardless of how good the idea sounds:

- The candidate's "innovation" can be expressed as "X but with Y also" where Y is a published method → cap at 0.5.
- The candidate's "innovation" requires a new dataset/benchmark to evaluate → cap at 0.7 unless the new benchmark is itself a contribution (then it should be presented as such).
- The candidate is "method X applied to domain Y" without a domain-specific reason → cap at 0.4.
- A near-identical paper exists in `literature_pool.json` (caught by re-search after Round 3) → score 0, kill the candidate.
- The candidate is mainly a benchmark sweep, leaderboard comparison, prompt bake-off, or evaluation matrix without a new method, formulation, theory, dataset/task, or falsifiable scientific claim → cap at 0.2 and usually kill.

## Feasibility score (0–1)

The question: can we actually execute this within the budget in `run.yaml`?

| Score | Label | What it looks like |
|---|---|---|
| 0.9–1.0 | Easy fit | Single-GPU, < 30% of budget, well-known training pipeline, datasets already on disk. |
| 0.7–0.89 | Comfortable | Within budget with margin, may need 1 new dataset download, training pipeline is standard. |
| 0.5–0.69 | Tight fit | Will use 70–95% of budget. May need to drop some seeds or ablations. Plan must be careful. |
| 0.3–0.49 | Risky | Within budget only if everything works first try. One bad run and we're over. Stage 2 must explicitly de-risk. |
| 0.0–0.29 | Infeasible | Doesn't fit budget at any plausible compression. Kill. |

### How to compute

Decompose the experiment into:

1. **Pretraining / fine-tuning compute.** Hours per run × number of runs.
2. **Inference / evaluation compute.** Hours per benchmark × number of benchmarks.
3. **Number of seeds for the main result.** ≥ 3 for credible error bars; 5 is standard.
4. **Number of ablation runs.** ≥ 2 (one to validate each claimed component).
5. **Buffer for debugging / failed runs.** Multiply by 1.3.

Total estimated GPU-hours = (1 + 2) × seeds + ablations × seeds × buffer.

Compare against `run.yaml::budget.gpu_hours`. Also check `budget.hardware` matches what the method needs (a method that needs 80GB VRAM cannot run on `1×L40-48GB`).

### Anti-cheat checks

- "We can use a smaller model" — only valid if the smaller model is plausibly representative of the claim. Otherwise the result doesn't generalize and Stage 4 will get killed.
- "We'll just use the public eval results" — only valid if the eval is on a standard benchmark with locked test sets. Otherwise the comparison isn't apples-to-apples.
- "We can do 1 seed" — never. 1-seed results are not publishable. Revise scope or kill.

## Contribution-shape score (0–1)

The question: is this a real research contribution, or are we sliding into an evaluation paper by accident?

| Score | Label | What it looks like |
|---|---|---|
| 0.9–1.0 | Clear research contribution | New mechanism, new formulation, new theory, or a new dataset/task with a sharp scientific claim. |
| 0.7–0.89 | Strong contribution shape | Empirical work, but organized around a real hypothesis or intervention that teaches something new. |
| 0.5–0.69 | Borderline | Has a claim, but risks being read as "mostly evaluation" unless Stage 2 sharpens it. |
| 0.3–0.49 | Weak | Mostly comparisons, sweeps, or repackaging known components. |
| 0.0–0.29 | Evaluation trap | Benchmark paper, model ranking, or prompt recipe paper with no genuine research claim. Kill by default. |

### Anti-trap checks

- If the title could be rewritten as `An Evaluation of ...` with no loss of substance, cap at 0.3.
- If removing the benchmark table would leave no contribution, cap at 0.2.
- If the work has no intervention beyond "compare methods across settings", cap at 0.2.
- If the claimed novelty is only "we evaluate on more datasets", cap at 0.2 unless the dataset suite itself is the contribution and the user explicitly wants that paper type.

## Combined score for autonomous mode

When `--autonomous` is set, the orchestrator picks the candidate with:

```
combined_score = 0.45 * novelty + 0.30 * feasibility + 0.25 * contribution_shape
```

We weight novelty highest because:
- A high-feasibility but low-novelty paper goes to a workshop at best.
- A benchmark-heavy paper can look deceptively feasible, so contribution shape gets explicit weight.
- A high-novelty but borderline-feasibility paper, *if* it works, is high-impact. The risk is real but worth it within the established budget gate (Rule 5).

Tie-break by: lower expected GPU-hours wins (cheaper to retry).

## What scores look like in `candidates.json`

```json
{
  "id": "C1",
  "title": "Adaptive Verifier-Guided Decoding for Small LMs at Test Time",
  "novelty_score": 0.74,
  "novelty_justification": "Closest works (canonical_ids: arxiv:2403.xxxx, arxiv:2405.yyyy) propose verifier-based decoding but with fixed verifier-step ratio. This proposes adapting the ratio per-token based on a learned uncertainty signal — addresses the 'verifier-step calibration' gap raised by both the Theorist and the Engineer in cluster C4.",
  "feasibility_score": 0.62,
  "feasibility_justification": "Estimated 28 GPU-hours of 40 budgeted (5 seeds × main + 2 ablations × 3 seeds × 1.3 buffer). Tight, but well within 1×H100. Risk: needs to fine-tune both a small LM (cheap) and a verifier (medium). If verifier training requires more than 4 hr per seed, drops to 0.45.",
  "contribution_shape_score": 0.86,
  "contribution_shape_justification": "The core contribution is a new adaptive decoding mechanism with a falsifiable efficiency-vs-accuracy claim, not a broad model ranking exercise.",
  "combined_score": 0.730
}
```

## When the rubric is wrong

The rubric is a tool, not an oracle. Override with a written justification when:

- A candidate scores low on novelty but is the *first* attempt at a clearly important problem nobody has tackled — bump 0.1, note in justification.
- A candidate scores high on feasibility but suspiciously so — usually the LLM underestimated something. Re-check with the Engineer persona.

Never override silently. The override goes into `candidates.json::manual_override` with reason.
