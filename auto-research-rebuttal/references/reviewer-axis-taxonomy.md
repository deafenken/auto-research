# Reviewer Axis × Severity Taxonomy

`ingest_openreview.py` uses this table to tag each atomic comment. The
labels propagate verbatim to `rebuttal.md` so every paragraph carries
its severity / axis chip. Edit the JSON if a heuristic mistag matters.

## Axes (one per atom)

| Axis | Reviewer phrases that point to it |
|---|---|
| **soundness** | "incorrect", "unsupported", "ablation missing", "OOD untested", "fails to", "doesn't generalise", "no significance test", "no error bars" |
| **clarity** | "unclear", "hard to follow", "notation", "Section X is dense", "definition", "what is" |
| **novelty** | "incremental", "very similar to", "already known", "Smith et al. 2023", "this just" |
| **significance** | "limited impact", "narrow", "would be more interesting if", "real-world relevance" |
| **presentation** | "typo", "Figure X", "Table caption", "minor", "rephrase" |

## Severity (one per atom)

| Severity | Triggers |
|---|---|
| **blocking** | "I cannot accept", "fundamental flaw", "this invalidates", "score would be 1" |
| **major**    | "would significantly improve", "I expect ablation X", "without this, my score is below threshold" |
| **minor**    | "nit", "typo", "consider", "small", "would be nice" |

When in doubt, prefer **major** over **minor** — a wrongly-classified
minor that turns out to be major is the most costly failure mode here
because the rebuttal will skip it.

## Stance taxonomy (used by `evidence-anchoring.md`, drafted into `rebuttal.md`)

| Stance | When to use |
|---|---|
| `REBUT-WITH-EVIDENCE` | An existing artifact under `runs/<id>/` already answers the concern |
| `CONCEDE-AND-PATCH`   | The reviewer is right; we patch `paper.tex` and acknowledge |
| `OUT-OF-SCOPE`        | The atom asks for something the venue's CFP explicitly excludes |
| `NEW-EXPERIMENT-NEEDED` | Major / blocking severity, no existing evidence — escalates per `escalation-thresholds.md` |
