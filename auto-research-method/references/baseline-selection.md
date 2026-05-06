# Baseline Selection

Choosing baselines is where many otherwise-good papers die in review. The rule is simple: compare against the **strongest, most recent** competitor your method should plausibly beat. Anything weaker reads as cherry-picking.

## The recency rule

Default cutoff: a baseline must be ≤ 24 months old (paper publication, not arXiv first-version), unless:

- It is the *de facto* standard against which everyone in the subarea reports (e.g. ResNet-50 on ImageNet for some pretraining ablations) — but always supplement with a recent comparison.
- The recent SOTA is closed-source / unreproducible (state this explicitly and cite it as "concurrent / not reproducible").

If you cannot find a 24-month baseline, that's a signal that either (a) the subarea is dormant or (b) you missed something in the literature pool. Check (b) first.

## The fairness rule (compute matching)

Baselines must be matched on:

| Axis | When it matters | What to match |
|---|---|---|
| Pretraining compute | Methods involving fine-tuning | Same base model, same fine-tuning compute |
| Inference FLOPs | Methods with variable inference (sampling, search) | Equal FLOPs per query |
| Training data | Methods involving data augmentation / synthesis | Same source dataset, same total tokens / images |
| Wall-clock | Latency claims | Same hardware, same batch size |
| Hyperparameter sweep budget | Always | Same number of HP configs explored per method |

The single most common reviewer complaint: "your method outperforms because it gets more compute." Pre-empt explicitly.

## Categories of baselines you must include

For most papers, your baseline set should span 3 categories. Missing any one weakens the paper.

### A. Trivial floor

The cheapest plausible baseline. Establishes that the problem is non-trivial.

- LLM tasks: greedy decoding, single-shot zero-shot.
- Classification: linear probe on frozen features, or last-layer logistic regression.
- RL: random policy (or behavior cloning if demonstrations are available).
- Generation: one-shot prompt to a base model.

### B. Strong contemporary

The published SOTA-or-near-SOTA in the subarea, ≤ 24 months old.

- Pull from `literature_pool.json` — the highest `influential_citation_count` in the subarea.
- Must be reproducible (open code preferred; otherwise the paper must report enough to reproduce).
- Should be in the same "regime" (same model size class, same data scale).

### C. Method-family alternative

If you propose method M, include another method that addresses the same problem with a *different* mechanism. This shows your specific design choice (not just "any method") is what wins.

- Example: if M is "verifier-guided decoding," include a "self-consistency" baseline (different mechanism, same problem).
- Example: if M is "LoRA variant," include a "prefix-tuning" or "(IA)^3" baseline.

## Forbidden baseline patterns

Each of these is a reviewer-killer. Do not do them.

### "We compare to the original Transformer."

If the original Transformer is your only comparison in 2026, you've ignored 7 years of progress. Cite it for context, then compare to recent work.

### "We compare to a baseline we trained ourselves with non-standard settings."

If the baseline's published number is X and you re-run it and get Y < X, you must:

1. Try harder to reproduce X (same code, same data, same hyperparameters).
2. If still unable, report both numbers and explain.
3. NEVER silently report Y as "the baseline."

### "We compare on a benchmark our method was designed for."

If you propose method M *for* benchmark B, then beating other methods on B is not strong evidence that M generalizes. Test on B *and* on a benchmark your method was not specifically designed for.

### "The baseline uses 1/4 of our compute, and we beat it."

Compute-matching, see above. If you genuinely cannot match (e.g. baseline only released a 7B variant, you have 70B), document it as a *limitation*, not a wash.

### "We compare to SOTA, where SOTA is whatever we can win against."

If the literature pool has 5 candidate SOTA methods at the same recency, you don't get to pick the easiest 2. Either include the full set (preferred) or justify the subset (limited compute → pick by random or by "most-cited").

### "Concurrent work is excluded."

If a paper appeared on arXiv ≤ 3 months before submission, you may discuss it as concurrent and not include it as a baseline. But if it appeared ≥ 3 months before, exclusion is suspect.

## The "Reviewer 2" baseline check

Before locking the baseline list, ask: "If I were the most adversarial reviewer in this subfield, what baseline would I want to see that the authors omitted?"

Common omissions:

- The trivial-but-strong scaling baseline (e.g. "but a 4× larger model would solve this").
- The previous-paper-from-same-author (showing this isn't an incremental improvement).
- The prompting / zero-shot baseline (if your method requires training, prove training is needed).
- The retrieval baseline (if your method "memorizes" facts, prove RAG isn't simpler).
- The distillation baseline (if your method makes a model smaller, prove distillation isn't simpler).

If any of these apply to your method, include the baseline.

## Custom dataset rules

If you must propose a custom dataset (no existing benchmark fits), follow these rules:

1. **Justify** in the paper why no existing benchmark works.
2. **Open-source** the dataset (or pre-register that you will).
3. **Provide a strong baseline** specifically for the dataset (so future work has a starting point).
4. **Run your method AND ≥ 2 baselines** on a *related existing* benchmark — to show the gain isn't an artifact of your dataset's design.

Custom datasets without these checks read as "we made the test that we know we'll pass."

## Reproducibility-of-baseline contract

For every baseline marked `must_reproduce: true` in `experiment_plan.yaml`, Stage 3 must produce a reproduction within ±20% of the published primary metric.

If reproduction fails by > 20%:

1. Log the failure with the published reference, your reproduction config, and your number.
2. Try one round of debugging (paper's hyperparameters? same seed? same eval split?).
3. Escalate per `auto-research/references/escalation-policy.md::baseline_failure`.
4. Either find the bug, exclude with explanation, or kill the project.

## Presenting baselines in the paper

Standard table layout (see `auto-research-writing/references/table-style.md`):

```
        | Dataset A | Dataset B | Dataset C
--------+-----------+-----------+-----------
Trivial floor      | x.x        | x.x        | x.x
Best published Y20 | x.x        | x.x        | x.x
Best published Y23 | x.x        | x.x        | x.x
Method-family alt  | x.x        | x.x        | x.x
Ours (proposed)    | **x.x**    | **x.x**    | **x.x**
```

Bold the best per column. Underline second-best. Report mean ± std.

## Final checklist

Before sending the baseline list to Stage 3:

- [ ] At least 2 baselines, ideally 3-5.
- [ ] Each baseline ≤ 24 months old OR justified.
- [ ] All baselines reproducible OR explicitly noted as "not reproducible / cited as concurrent."
- [ ] Compute is matched, OR mismatch is documented.
- [ ] At least one baseline addresses the same problem with a *different* mechanism.
- [ ] No baseline appears to have been chosen because it's easy to beat.
- [ ] The "Reviewer 2 omission" check has been run.
