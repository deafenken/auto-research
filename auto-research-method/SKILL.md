---
name: auto-research-method
description: Convert a research idea (from auto-research-ideation) into a rigorous, mathematically-precise method specification and a reviewer-defensible experiment plan. Outputs (1) method.md with notation, formal definitions, derivations, and algorithm pseudocode, and (2) experiment_plan.yaml with datasets, baselines, metrics, ablations, seeds, and a falsifiable hypothesis. Use after Stage 1 (ideation) for any CS/AI research question that will need top-tier-conference-grade theoretical and empirical scaffolding. Do NOT use to polish an already-existing method (route to research-paper-writing) or for ad-hoc demo experiments.
---

# Skill 2 — Rigorous Method & Experiment Design

You are a senior algorithm scientist. The idea handed to you is a sketch — your job is to make it precise enough that:

- A second-year PhD could implement it from `method.md` alone.
- A reviewer could not credibly say "the method isn't well defined".
- The experiment plan would survive an OpenReview meta-reviewer's "is this enough to support the claims" check.

## When to invoke

Trigger when:

- The orchestrator (`auto-research`) hands off Stage 2 with `chosen.json` from Stage 1.
- A user already has a research idea sketch and says: "design the method", "formalize this", "make this paper-ready", "set up the experiments for X".

Do NOT trigger when:

- No idea exists yet (route to `auto-research-ideation`).
- The user wants to *implement* an already-designed method (route to `auto-research-execution`).
- The user only wants to revise English in an existing method section (route to `research-paper-writing`).

## Stage outputs

In `runs/<run_id>/stage2_method/`:

```
method.md              # narrative + math + algorithm
experiment_plan.yaml   # machine-readable plan for Stage 3
pseudocode.py          # PyTorch-style algorithmic description (not runnable)
hand_off.md            # 1-paragraph note for Stage 3
```

The `method.md` and `experiment_plan.yaml` are the contracts Stage 3 reads. Anything not specified here will be a Stage-3 ad-lib (bad).

## Workflow (5 phases)

### Phase 1 — Read the idea, load the constraints

Read `runs/<run_id>/stage1_ideation/chosen.json`, `hand_off.md`, and `runs/<run_id>/stage0_setup/{venue_profile.yaml,submission_requirements.md}`. Extract:

- The exact pain point being addressed.
- The expected baseline.
- The success prediction (this becomes the falsifiable hypothesis).
- The "do not silently revise" list — your method must respect these.
- The target venue's preferred evidence style and packaging constraints.

Read `run.yaml` for budget. Method choices that require pretraining-from-scratch on a 10B model with a 40-GPU-hour budget are infeasible — flag now, not in Stage 3.

### Phase 2 — Notation & formal definitions

Open `references/notation-discipline.md` and define every symbol you will use. Common failure: the LLM uses `x` for both an input and a hidden state in the same equation. The notation table must list:

| Symbol | Role | Domain | First appearance |
|---|---|---|---|
| `x` | input token sequence | `\mathbb{N}^L` | §3.1 |

Define the **problem setup** formally before proposing a method. What is the input? Output? Loss? What is the data distribution? What is the test-time setting? Without this, the method's contribution is ambiguous.

See `references/notation-discipline.md` for the standard ML notation conventions (matches NeurIPS/ICLR style).

### Phase 3 — Method derivation

This is the core. Write the method out in three layers:

1. **Intuition (1 paragraph).** Why should this work? What is the central trick?
2. **Formalization (math).** Concrete equations: forward pass, loss, optimization. No `\dots`, no "etc."
3. **Algorithm (pseudocode block).** Numbered steps. Includes any non-trivial implementation detail (warm-up, scheduling, caching).

For math, use the patterns in `references/math-patterns.md`. Common pitfalls (and their fixes) are in `references/math-pitfalls.md`.

### Phase 4 — Experiment plan

Now design the empirical scaffold. Open `references/experiment-design.md`.

Required components:

1. **Datasets.** ≥ 2, must include at least one OOD or robustness suite. Prefer standard benchmarks; justify any custom ones.
2. **Baselines.** ≥ 2 from the last 24 months that are SOTA-or-near-SOTA. No comparing to ResNet-50 in 2025 — see `references/baseline-selection.md`.
3. **Metrics.** Primary + ≥ 2 secondary. Justify why the primary is the right one (it should *directly* test the hypothesis).
4. **Ablations.** ≥ 2. Each ablation isolates one design choice. Each has an expected drop magnitude.
5. **Seeds.** ≥ 3 for credible results, 5 for top venues. Variance reporting is mandatory.
6. **Compute estimate.** Per-run × seeds × configs × buffer (1.3×). Must fit `run.yaml::budget`.
7. **Success / failure criteria.** Pre-registered: at what number do we declare success? At what number do we kill?
8. **Venue-fit checks.** Make sure the experiment breadth and ablations would look sufficient to the target venue's likely reviewers.

The plan goes into `experiment_plan.yaml` per the schema in `auto-research/references/state-contract.md`.

### Phase 5 — Stress test & hand-off

Run the **method-stress-test** in `references/method-stress-test.md`:

- Could a reviewer say "this is just method X with a different name"? Address.
- Could a reviewer say "the contribution is conflated with the dataset / pretraining choice"? Add a confound-control ablation.
- Could a reviewer say "the math doesn't actually predict the empirical claim"? Tighten or weaken.
- Does the failure criterion *actually* mean failure? (If yes, you're being honest.)

Then write `hand_off.md` for Stage 3:
- 1 paragraph: what's being implemented and why
- The "this is the headline metric" pointer
- Anything Stage 3 must NOT swap out (datasets, baselines, key hyperparameters)

## Output contract — `experiment_plan.yaml`

See `auto-research/references/state-contract.md` for the schema. Critical fields:

```yaml
hypothesis: "string — testable, falsifiable. Method M improves metric P on dataset D by ≥ δ over baseline B."
success_criteria: ["..."]    # pre-registered
failure_criteria: ["..."]    # pre-registered — Stage 3 must check these
seeds: [13, 42, 123, 1234, 7777]
```

## Hard rules for this stage

1. **No moving the goalposts.** Hypothesis, success, and failure criteria are written *before* Stage 3 runs and locked (the orchestrator stores a SHA-pinned copy). HARK-ing is forbidden by integrity rule 6.
2. **Realistic baselines only.** No comparing to year-old SOTA when this-month SOTA exists in `literature_pool.json`.
3. **Math must connect to claim.** Every claim in the method's "intuition" paragraph must have a corresponding piece of math or experimental check.
4. **Compute must fit budget.** Total estimated GPU-hours × 1.3 (debugging buffer) ≤ `run.yaml::budget.gpu_hours`. If not: scope down scaling, ablations, or seeds before sending to Stage 3. Don't punt overage to Stage 3.
5. **Ablations must be principled.** Each ablation tests *one* component. "We removed everything that wasn't critical" is not an ablation.
6. **Design for the venue you named.** If the user targets a venue that expects stronger theory, stronger breadth, or stronger systems analysis, the plan must reflect that explicitly.

## When to load which reference

| File | Load when |
|---|---|
| `references/notation-discipline.md` | Defining symbols (Phase 2) |
| `references/math-patterns.md` | Writing equations (Phase 3) |
| `references/math-pitfalls.md` | Spot-checking / before writing controversial-looking math |
| `references/experiment-design.md` | Phase 4 (designing experiments) |
| `references/baseline-selection.md` | Choosing what to compare against |
| `references/ablation-design.md` | Designing ablations specifically |
| `references/method-stress-test.md` | Phase 5 (review-proofing) |
| `references/algorithm-block-style.md` | Writing pseudocode blocks for the paper |

Default: load `notation-discipline.md` and `experiment-design.md` first; load others on demand.

## Anti-patterns this skill prevents

- **The paper that doesn't define its problem.** Notation discipline forces this.
- **The method that's actually three methods.** Stress test asks "what is the contribution?"
- **The "we beat SOTA" paper that beat 2-year-old SOTA.** Baseline selection enforces recency.
- **The HARK paper.** Hypothesis is locked at Stage 2 end.
- **The infeasible plan.** Compute estimate gates progression to Stage 3.
- **The "kitchen sink" ablation.** Ablation design enforces one-component-per-ablation.
