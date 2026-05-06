# CFP Innovation Lens

Use this after Stage 0 has collected the target venue's CFP, scope, track description, and review emphasis.

## Goal

Convert venue language into idea-selection pressure. Do not just ask "is this idea novel?" Ask "is this the kind of novelty this venue is willing to reward?"

## Extract these signals from the CFP

1. Preferred contribution type:
   - algorithmic novelty
   - empirical breadth
   - systems efficiency
   - benchmark or dataset contribution
   - theory or guarantees
2. Reviewer expectations:
   - strong ablations
   - real-world impact
   - robustness / safety / OOD
   - deployment evidence
3. Anti-patterns:
   - incremental metric gains
   - weak baselines
   - narrow evaluation
   - poor reproducibility

## Turn CFP signals into questions

For each candidate idea, ask:

- Why would this venue want this now?
- What kind of evidence would make reviewers believe it?
- What would make reviewers call it incremental?
- What section of the CFP does this idea naturally map to?

## Scoring heuristic

High venue-fit ideas usually satisfy at least two:

- match a plainly stated CFP priority,
- address a current reviewer pain point for that venue,
- produce evidence in the style the venue rewards,
- avoid a known venue-specific anti-pattern.

Low venue-fit ideas often look like:

- solid work aimed at the wrong audience,
- clever methods with no evaluation style the venue respects,
- benchmark chasing when the venue is asking for insight,
- theory-heavy framing for a venue expecting broad empirical evidence.

## Output requirement

Each surviving candidate should include one sentence answering:

`Why this venue, not just why this topic?`
