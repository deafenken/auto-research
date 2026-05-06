# Page Budgeting

Use this after Stage 0 has identified the target venue's page rules.

## Priority

1. obey the venue's main-text page limit,
2. preserve enough detail for method and results to be reviewer-defensible,
3. make `Related Work` feel genuinely well-read rather than thin or perfunctory.

## Default section budget

For a standard top-tier ML conference paper with about 8 to 10 main-text pages:

- `Introduction`: 1 to 1.5 pages
- `Related Work`: 1 to 1.5 pages
- `Method`: 2 to 3 pages
- `Experimental Setup`: 0.75 to 1.25 pages
- `Results + Ablations`: 2 to 3 pages
- `Limitations + Conclusion`: 0.5 to 1 page

This is a starting point, not a law. Shift space based on venue and contribution type.

## Related Work policy

Default target:

- make it rich in references,
- usually around 1 to 1.5 pages,
- cluster papers by line of work instead of listing them one by one,
- explicitly position the paper against the closest 3 to 8 works.

Do **not** shrink Related Work to a token half-page unless:

- the venue page limit is unusually strict,
- the venue expects a compressed related-work style,
- or the contribution genuinely needs more space in Method / Results to stay credible.

## Citation density guidance

Good signals:

- each paragraph in `Related Work` references multiple relevant papers,
- the closest prior work is discussed concretely, not name-dropped,
- the section explains what prior work did and where the gap remains.

Bad signals:

- only a few citations total,
- one-paper-per-sentence name dumping,
- generic "many works have studied..." filler,
- shrinking citations just to save space.

## If over page limit

Trim in this order:

1. repetitive introductory motivation,
2. duplicated setup details that can move to appendix,
3. verbose prose around tables,
4. overly broad background paragraphs.

Do **not** first cut:

1. the core method definition,
2. the main results interpretation,
3. the closest-prior-work comparison,
4. the limitations section.

## Output expectation

When Stage 4 finishes drafting, it should be able to state:

- target venue page limit,
- estimated main-text page usage,
- whether `Related Work` landed in the intended range,
- what tradeoffs were made if it did not.
