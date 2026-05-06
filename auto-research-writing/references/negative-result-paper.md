# Negative-Result Framing

Use this when the pre-registered success criteria were not met.

## What changes

- The contribution becomes: a falsified hypothesis, a careful diagnosis, or a benchmark/reproduction lesson.
- The abstract must say the primary claim did **not** hold.
- The introduction should motivate why falsifying this hypothesis matters.

## Acceptable paper shapes

1. `Failure with explanation`: the method failed, but ablations identify why.
2. `Reproduction gap`: a claimed baseline or prior result does not reproduce under controlled conditions.
3. `Boundary condition`: the idea works only under a narrower regime than expected.

## What is forbidden

- Hiding the failed main metric behind a positive secondary metric.
- Rewriting the original Stage 2 hypothesis.
- Omitting the strongest baseline because it hurts the story.

## Required language

Use direct phrasing such as:

- `We do not observe the pre-registered improvement on ...`
- `The proposed mechanism appears insufficient under ...`
- `Our evidence narrows the regime where ... may be beneficial`
