# Integrity Rules — Mandatory at Every Stage Transition

These are the non-negotiable rules. The orchestrator enforces them; sub-skills implement them. If any check below fails, **stop and surface to the human** — do not patch over.

This document is loaded at every stage transition (Stage 1→2, 2→3, 3→4, and within Stage 4's revision loops).

## Rule 1 — Numbers must trace to a file

**Statement.** Every numeric claim in `paper.tex` must be reproducible from a row or aggregation of rows in `results.csv`. No "approximately", no "roughly".

**Check (run before LaTeX compilation).**

```bash
# pseudocode
for each \\textbf{N.NN} or "N.NN%" in paper.tex:
    grep that number (and ±0.005 neighbors) in results_summary.json
    if no match → BLOCK compilation, report missing trace
```

**Failure mode this prevents.** "Made-up SOTA improvements" — the most common cause of withdrawn-post-acceptance papers in CS.

**Allowed exception.** Numbers cited from prior work (e.g. "Vaswani et al. report 28.4 BLEU") — those need a `\cite{}` and the number must appear in the cited paper's abstract or main table. Verify by fetching the paper text.

## Rule 2 — Citations must resolve to real papers

**Statement.** Every `\cite{key}` must:

1. Have a corresponding entry in `references.bib`.
2. The bib entry's DOI or arXiv-ID was returned by Semantic Scholar / OpenReview / arXiv API in the current run.
3. The cited paper's title and first author match.

**Check.**

- Build a manifest `runs/<id>/stage1_ideation/literature_pool.json` of every paper Stage 1 verified.
- Stage 4 may only `\cite{}` keys that map to entries in this manifest, OR to new papers fetched mid-writing through the same verification route.
- A linter scans `paper.tex` for `\cite{}` keys not in the manifest → BLOCK.

**Failure mode this prevents.** Hallucinated references — a recurring failure mode of LLM-written papers (e.g., "Smith et al. 2023" with a plausible-sounding but nonexistent title).

**See also.** `auto-research-ideation/references/citation-verification.md` for the verification protocol.

## Rule 3 — No silent baseline downgrade

**Statement.** Baselines listed in `experiment_plan.yaml` are a contract. If a baseline cannot be made to run, the only allowed responses are:

- Spend more time debugging it (logged in `run_report.md` as "Failed runs").
- Replace it with a *stronger* alternative (more recent SOTA, not weaker).
- Escalate to the human and document the substitution in `run_report.md` under "Deviations".

**What is forbidden.** Quietly dropping a strong baseline, or replacing it with a weaker one, so the proposed method "wins".

**Check.** At Stage 3→4 transition, diff `experiment_plan.yaml::baselines` against `results.csv::config_name`. Every planned baseline must appear in results OR be explicitly marked as `failed_to_run` in `run_report.md` with a traceback.

**Failure mode this prevents.** Cherry-picked baselines — a frequent reviewer complaint that sinks otherwise sound papers.

## Rule 4 — Reproducibility floor

**Statement.** Every entry in `results.csv` must include:

- `git_commit` (SHA from the `code/` repo)
- `seed`
- `config_name` (which YAML in `code/configs/` was used)
- `gpu_hours`
- Hardware string (matches `run.yaml::budget.hardware`)

A row missing any of these is `INVALID`.

**Check.** Pre-Stage-4 lint:

```python
import pandas as pd
required = {"git_commit", "seed", "config_name", "gpu_hours", "primary_metric"}
df = pd.read_csv("results.csv")
missing = required - set(df.columns)
if missing: raise SystemExit(f"results.csv missing required cols: {missing}")
nulls = df[list(required)].isnull().any(axis=1).sum()
if nulls: raise SystemExit(f"{nulls} rows with null required fields")
```

**Failure mode this prevents.** Numbers that nobody — not even the author — can reproduce six months later.

## Rule 5 — Compute budget gate

**Statement.** Cumulative GPU-hours, summed across all runs in `results.csv`, must not exceed `run.yaml::budget.gpu_hours`.

**Checks.**

- At 50% consumed → log a warning to the user.
- At 80% consumed → pause, surface remaining-budget vs. remaining-experiments, ask: "narrow scope, ask for more budget, or proceed?"
- At 100% consumed → **hard stop**. No new runs. Writing stage uses whatever results exist.

**Failure mode this prevents.** Runaway compute spend — common in autonomous-mode failures where the agent retries a broken experiment indefinitely.

## Rule 6 — Hypothesis honesty

**Statement.** The hypothesis written in `experiment_plan.yaml::hypothesis` may not be edited after Stage 3 begins. If results contradict it, the paper says so.

**What is allowed.**

- Adding a *new* hypothesis informed by results (clearly labeled "post-hoc") and testing it in a follow-up run.
- Reframing the contribution in writing (e.g. "we found X failed but Y emerged"), as long as the original prediction is preserved in the paper's discussion.

**What is forbidden.** Editing `experiment_plan.yaml::hypothesis` retroactively to match results. The orchestrator stores a SHA-pinned copy at Stage 3 start in `stage3_execution/hypothesis_locked.txt` and diffs against it before allowing Stage 4.

**Failure mode this prevents.** HARK-ing (Hypothesizing After Results are Known) — academic-fraud-adjacent and reviewer-detectable.

## Rule 7 — Boundary on "auto-fix"

**Statement.** Stage 3 may auto-recover from these failure classes without escalation:

- CUDA OOM → halve batch size, restart (max 3 times).
- Transient network / dataset download failures → exponential backoff (max 5 retries).
- A single seed's run hangs → kill and rerun once.

Any other class — silent NaN loss, model architecture mismatch, unexpected metric collapse — escalates after **5 failed debug iterations**, with the full traceback chain.

**Failure mode this prevents.** The agent "fixing" by deleting the failing test, weakening assertions, or commenting out the broken module.

## Rule 8 — No accidental evaluation-paper drift

**Statement.** Unless the user explicitly requested an evaluation / benchmark paper, Stage 1 and Stage 2 must preserve a genuine research contribution: a new mechanism, formulation, theory, dataset/task, or falsifiable scientific hypothesis.

**What is forbidden.**

- Letting the idea drift into "we evaluated many models on many benchmarks."
- Reframing a weak method paper as a broad comparison paper just because execution is easier.
- Treating benchmark breadth alone as novelty.

**Check.** At Stage 1→2 and 2→3 transitions, inspect `candidates.json`, `chosen.json`, `method.md`, and `stress_test.md`. If the contribution cannot survive removal of the benchmark table, BLOCK and re-scope.

**Failure mode this prevents.** The common autonomous-agent trap where "real innovation is hard, so the system quietly degenerates into a benchmark or evaluation paper."

## Enforcement summary table

| Rule | Stage where checked | Mode |
|---|---|---|
| 1. Numbers trace | 4 (pre-compile) | Block |
| 2. Citations real | 1, 4 | Block |
| 3. No baseline downgrade | 3→4 | Block |
| 4. Reproducibility floor | 3→4 | Block |
| 5. Compute budget | continuous in 3 | Warn @ 50%, ask @ 80%, hard stop @ 100% |
| 6. Hypothesis locked | 3, 4 | Block |
| 7. Auto-fix boundary | 3 | Escalate after 5 |
| 8. No evaluation-paper drift | 1→2, 2→3 | Block |

## When a rule is violated

1. Stop the current stage immediately.
2. Write a clear failure note to `runs/<id>/violations.log` with: which rule, what evidence, what the agent was about to do.
3. Surface to the human with the rule name and the offending artifact.
4. Do not retry until human approval is given.

These rules are not suggestions. They exist because every one of them maps to a documented failure mode in published-then-retracted papers or fired-then-retried agent runs.
