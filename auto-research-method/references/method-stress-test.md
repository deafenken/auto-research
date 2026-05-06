# Method Stress Test

Phase 5 of Skill 2: before handing off to Stage 3, simulate the most adversarial reviewer and answer their questions in advance. Most papers get rejected for issues a 30-minute stress test would have surfaced.

## The 8 questions

For each, write a paragraph in `method.md` (visible in the paper) or in `runs/<id>/stage2_method/internal_notes.md` (for your records).

### Q1. "Is this just method X under a different name?"

For each of the 3 closest works in `literature_pool.json` (the "expected baselines" in the chosen idea), explicitly state:

- What X does
- What you do
- The non-trivial difference

If you can't articulate a non-trivial difference, the contribution is too small. Either find a real one, or kill.

### Q2. "Does the math actually predict the empirical claim?"

Walk through the math in `method.md`. The key equations should imply (or at least be consistent with) the empirical hypothesis.

Example:

- Hypothesis: "Method M reduces calibration error by lowering temperature when uncertain."
- Math should: derive an explicit relationship between input uncertainty and selected temperature, and show this lowers ECE under reasonable assumptions.

If the math is decorative (doesn't connect to the prediction), reviewers will say so. Either tighten the math or weaken the claim to match what the math supports.

### Q3. "What is the simplest alternative explanation for the expected gain?"

For each component of your method, ask: "Is there a simpler explanation for why this might help, that has nothing to do with my proposed mechanism?"

Examples:

- "We use longer thinking" → simpler explanation: more compute = more chances to get lucky.
- "We use a verifier" → simpler explanation: verifier acts as a regularizer / model averaging.
- "We use a learned adaptive parameter" → simpler explanation: the learned value just happens to land near a known good fixed value.

For each simpler explanation, design an ablation that distinguishes your mechanism from it. Add to the ablation list.

### Q4. "How does this fail?"

The method must have a failure mode. Identify it now (in `method.md`'s Limitations subsection) so it isn't a Stage-4 surprise.

Common failure modes:

- Distribution shift: works on benchmark, fails OOD.
- Scale: works at 1B, fails at 70B (or vice versa).
- Domain: works on text, fails on code.
- Compute regime: works under abundant compute, fails under tight budget.
- Adversarial inputs: works on natural data, breaks on crafted inputs.

Predict which one applies. Stage 3 may verify or refute the prediction — either is a finding.

### Q5. "What is the cheapest experiment that would refute the central claim?"

If you can't think of one, the claim isn't falsifiable, and the paper isn't science. Write the experiment. Plan to run it.

Often this is the "compute-matched comparison": if your method uses 4× compute, the cheapest refutation is showing the baseline matches you when given 4× compute too.

### Q6. "Is the dataset / benchmark choice biased toward my method?"

Run through the chosen datasets and ask:

- Does the dataset's construction (training data, eval split, evaluation metric) accidentally favor methods of your style?
- Is there a benchmark you *avoided* because it would be hard for your method? (If yes — include it.)
- Would the gain replicate on a randomly-chosen subset of the dataset, or only on certain kinds of examples?

If you find bias, include the additional benchmark or sub-analysis.

### Q7. "If I had infinite compute, would my method still matter?"

Some methods are "compute trade-offs": they get more performance per FLOP, which only matters if FLOPs are scarce. Others give an *absolute* gain that compute can't replicate.

Be honest about which yours is. If it's a compute trade-off:
- Frame the contribution as "efficient X" not "better X."
- Show the FLOP-matched curve where you are above the baseline at every compute point.

If it's an absolute gain:
- Show that the gap *persists* as compute increases (otherwise you're really back to a trade-off).

### Q8. "What would be in Reviewer 2's most damning comment?"

Generate it. Then address it in the paper.

Format:

```
> "The proposed method appears to add complexity without commensurate benefit. The gain reported in Table 1 (0.7pp on benchmark X) is within the noise of the cited baselines, and the ablations only confirm components the authors designed. The work feels incremental."

Response: ...
```

If you can't write a credible response, the paper has a real weakness. Address it (with more compute, more ablations, sharper framing) before Stage 3.

## Output

Write the stress-test results to `runs/<id>/stage2_method/stress_test.md`. Some answers belong in the public paper (Limitations section); others are internal.

The orchestrator reads `stress_test.md` at Stage 2 → Stage 3 transition and surfaces any "unanswered" stress questions to the user before allowing Stage 3 to begin.

## Anti-pattern: the cosmetic stress test

Don't write Q1-Q8 with one-line non-answers. The point is to find weaknesses. If after the stress test you found nothing, you didn't try hard enough — most likely Q3 (alternative explanations) is the one you skipped.

A real stress test that catches a real weakness is *cheaper than re-running Stage 3 after a reviewer catches it*.
