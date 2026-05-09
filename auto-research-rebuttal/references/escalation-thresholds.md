# Escalation Thresholds

Phase 5 must surface to the human if any of these triggers fires.
Mirrors the spirit of `auto-research/references/escalation-policy.md`
but is specific to rebuttal dynamics.

## Hard escalation (stop, ask the user)

1. **Big-budget new experiments.** Any atom labelled `NEW-EXPERIMENT-NEEDED`
   whose estimated cost > 20% of `run.yaml::budget.gpu_hours - gpu_hours_consumed_so_far`.
   Why: a reviewer cannot realistically expect a budget-doubling experiment
   inside a rebuttal window, and silently committing to one wastes user time.
2. **Convergent blockers.** ≥2 reviewers flag the same `blocking` concern
   AND none of them resolves to a `REBUT-WITH-EVIDENCE` stance. The
   paper has a structural issue; don't paper over it.
3. **Self-review collapse.** The Phase-5 strict-prompt auto-reviewer
   estimates the rebuttal would change the hypothetical Reviewer-2
   score by ≤ 0 points. The rebuttal isn't doing its job.
4. **Edits without diff.** `paper.tex` was modified during Stage 5 but
   `revision_diff.md` is empty. This is the Rule-9 trip; the
   orchestrator will block, but `escalation-thresholds.md` documents
   the contract here for the user.

## Soft escalation (continue, but flag)

* Any `OUT-OF-SCOPE` stance where the cited CFP quote is older than 24
  months — venues update their scope.
* > 30% of atoms classified as `presentation` in a single review — the
  reviewer is signalling the paper isn't ready in their eyes; consider
  asking the user whether to invest in another round of writing.
* Any `CONCEDE-AND-PATCH` whose patch grows the paper past the venue
  page limit. Trade off with another section before sending.

## What "escalate" means in practice

Append a section to `hand_off.md`:

```markdown
## ESCALATIONS — needs human

- [trigger=big-budget-new-experiment] Atom R2.A4 wants a 24 GPU-h
  ablation on a benchmark we don't currently support. Remaining budget
  is 10 GPU-h. Suggest: respond as Limitation, schedule for v2.
```

Do NOT block silently. Do NOT proceed to send the rebuttal. The user
decides whether to commit, descope, or move to a Limitation.
