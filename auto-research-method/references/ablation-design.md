# Ablation Design

Ablations are the part of an experiment plan that converts "we propose method M and it works" into "we propose method M, and here is *why* it works." Without good ablations, reviewers will write "the gain could be from any of three things in the method; the authors don't disentangle."

## The principle: one component per ablation

Each ablation isolates exactly one design choice. If you change two things at once, you cannot attribute the result to either.

Bad ablation:

> "We removed the verifier head AND replaced cosine annealing with constant LR."

Good (split into two):

> "Ablation 1: remove verifier head, keep cosine annealing → gain drops from +5pp to +1pp.
>  Ablation 2: keep verifier head, replace cosine annealing with constant LR → gain drops from +5pp to +4pp."

Now you know the verifier is doing most of the work.

## What to ablate

For a method with `N` design choices, you do not need `2^N` ablations (the full factorial). You need `N` ablations: each one removes / replaces one component. Optionally add interactions for the top 2-3 most surprising components.

### Default ablation set for a typical method

- **A1 — Component-removal.** For each major novel component C in your method, run "M without C." If "without C" is incoherent (the method falls apart), replace C with the simplest substitute.
- **A2 — Sensitivity to a key hyperparameter.** Pick the single most-important new hyperparameter and sweep it across 3-5 values, including 0 (or the natural "off" value). Show monotonic / smooth behavior — if your method is wildly hyperparameter-sensitive, that's a finding.
- **A3 — Method-family alternative.** Replace your novel mechanism with a *cheaper / simpler* mechanism that does the same job. If the simpler mechanism gets close, your contribution shrinks.
- **A4 — Scale variation.** If feasible, test on at least one smaller and one larger model size — does the gain hold?
- **A5 — Architecture / backbone variation.** If feasible, test on at least one alternative backbone — does the gain transfer?

A1 is required. A2-A5 depend on the method and budget.

## Pre-registering expected outcomes

For each ablation, write down the *expected* result before running it. This is in `experiment_plan.yaml`:

```yaml
ablations:
  - name: "A1_remove_verifier"
    description: "drop the verifier head, keep adaptive temperature"
    expected_drop: ">= 2pp accuracy"
    purpose: "show the verifier is a primary source of gain"
    interpretation_if_smaller_drop: "verifier matters less than expected; main gain is from temperature scheduler — pivot the paper's framing"
    interpretation_if_larger_drop: "verifier is even more critical; emphasize this in writing"
```

Pre-registration is the difference between "ablation as scientific check" and "ablation as paper-decoration." Reviewers can tell.

## What to do when an ablation surprises you

The point of ablations is to be surprised sometimes. When it happens:

### Smaller-than-expected drop

Means: the component you thought was critical isn't. Your method's contribution may be smaller than the headline implies.

**Honest options:**
- Re-frame the paper around the *actual* source of gain (often this is a stronger paper).
- Demote the headline number — the gain attributable to your novel contribution alone may be smaller than the total method gain.
- Add a follow-up ablation to identify what *is* doing the work.

**Forbidden:**
- Quietly drop the ablation from the paper.
- Re-run the ablation with a different hyperparameter setting until the drop appears.

### Larger-than-expected drop

Means: the component is more critical than you thought. This is good — it strengthens the paper.

- Highlight it in the writeup: "Removing C causes the largest performance drop, suggesting it is the primary source of gain."
- Consider adding A2-style sensitivity analysis on this component.

### Non-monotonic sweep

Means: your component has a "sweet spot" you didn't know about. This is a finding.

- Report the full sweep, not just the best point.
- Discuss the non-monotonicity in the paper. Often this opens a follow-up paper.

## Common ablation pitfalls

### Pitfall 1: ablation = "we removed everything."

```
[BROKEN]
Ours: 0.85
Ours w/o everything: 0.50  ← no information here
```

The "kitchen sink ablation" tells you nothing. Each row should remove ONE thing.

### Pitfall 2: ablations only on the easy benchmark.

If your method works on benchmark A and fails on B, ablating only on A overstates the strength of the components. Run ablations on the same benchmarks as the main results.

### Pitfall 3: ablations with fewer seeds.

Reviewers will ask "is the ablation drop within seed noise?" Ablations should use ≥ 3 seeds. Cheap rule: ablations get 3 seeds (reduced from main's 5) if budget is tight.

### Pitfall 4: ablating the wrong granularity.

If your method has a 5-step pipeline, ablating "step 2 only" might be too fine-grained — the natural unit of the contribution is "the inner loop that combines steps 2-4."

Ablate at the granularity that matches *how the contribution is described in the abstract*.

### Pitfall 5: replacing with a non-naive substitute.

When you "remove" a component, what replaces it matters. If component C is "adaptive temperature" and you "replace with fixed temperature," what fixed value? Pick the most-natural default (e.g. 1.0 for softmax temperature, the published baseline for everything else). Document the substitute.

### Pitfall 6: omitting a baseline-exposing ablation.

If your method = "baseline + thing X," the most important ablation is "baseline alone." Without this, the gain might be entirely from the baseline you re-implemented better.

### Pitfall 7: ablation timing.

Don't run all ablations at the end after main results. Run a quick version of the most-likely-revealing ablation early, so if the contribution is mis-located, you find out before spending the full budget.

## How many ablations is enough

Too few: reviewers ask "what's actually doing the work?"
Too many: paper is exhausting; you exceed page limits.

Heuristic:

- Conference paper (8 main pages): 3-6 ablations.
- Workshop / short paper: 2-3 ablations.
- Journal: 5-10 ablations.

Each ablation should fit in a row of the main ablation table or a paragraph in the appendix.

## Compute budget for ablations

Ablations typically eat 30-50% of the total experimental compute. Plan for it:

```yaml
# rule of thumb
total_compute = (5 main seeds) * (1 main config) + (3 ablation seeds) * (5 ablation configs)
              = 5 + 15
              = 20 unit-runs
              # so ablations are ~75% of unit-runs but each unit may be cheaper
              # if ablations use a smaller eval subset
```

## Output format

In `experiment_plan.yaml`:

```yaml
ablations:
  - name: short_descriptive_id
    description: 1-line description of what changes
    purpose: 1-line description of what this ablation tests
    expected_drop: pre-registered expected effect with magnitude
    interpretation_if_smaller_drop: how the paper changes
    interpretation_if_larger_drop: how the paper changes
    seeds: 3
    relative_compute: 0.3     # fraction of a main run
```

In the paper, ablations land in their own table or section, near the main results. See `auto-research-writing/references/table-style.md` for layout.

## Final check

Before locking the ablation list:

- [ ] Each ablation removes/replaces *exactly one* component.
- [ ] Each ablation has pre-registered expected outcome.
- [ ] Each ablation has a clear "what would this tell us" purpose.
- [ ] Total ablation compute is ≤ 60% of the main experiment compute.
- [ ] Ablations cover at least: component-removal (A1), and one of A2-A5.
- [ ] Plan for "surprise" outcomes: each ablation has interpretations for both smaller and larger drops.
