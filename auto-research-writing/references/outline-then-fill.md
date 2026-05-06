# Outline-Then-Fill

Draft structure before prose.

## Section order

1. `Title`
2. `Abstract`
3. `Introduction`
4. `Related Work`
5. `Method`
6. `Experimental Setup`
7. `Results`
8. `Ablations and Analysis`
9. `Limitations`
10. `Conclusion`

## Section-specific guidance

- `Abstract`: problem, method, headline number, one caveat.
- `Introduction`: pain point, why current methods fail, contribution bullets.
- `Related Work`: cluster by approach, not by paper-by-paper summaries.
- `Method`: define symbols once; mirror Stage 2 notation.
- `Experimental Setup`: datasets, baselines, metrics, seeds, hardware.
- `Results`: start with the primary metric tied to the Stage 2 hypothesis.
- `Ablations and Analysis`: isolate components, include variance and failure cases.
- `Limitations`: compute, robustness, data, and external validity.
- `Conclusion`: summarize what was learned, not just what improved.

## Length discipline

- Spend most tokens on `Introduction`, `Method`, and `Results`.
- Keep `Related Work` and `Conclusion` compact unless the user asks for a survey-heavy paper.
- Avoid writing speculative future work that is not grounded in observed failure modes.
