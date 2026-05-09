# Evidence Anchoring Protocol

`anchor_evidence.py` consumes `reviews_ingested.json` and walks four
sources in **strict priority order** to produce `evidence_map.json`.
This is the same priority `trace_numbers.py` uses for numeric claims —
keep them in lockstep.

## Search order

1. `stage3_execution/results.csv` — every row's `config_name`, `notes`,
   and per-metric cells. Match by TF-IDF cosine over the atom text +
   each row stringified.
2. `stage3_execution/run_report.md` — split into sections (`## ...`)
   and TF-IDF the atom against each section's body.
3. `stage4_writing/claims_ledger.jsonl` — concatenate
   `metric + unit + source + paper_tex_locator` per entry.
4. `stage1_ideation/literature_pool.json` — `title + abstract`.

Stop after gathering ≤3 hits per source above the cosine threshold of
**0.25**. Below 0.25 the matches are noise — don't include them just to
look productive; the rebuttal will dilute.

## Stance recommendation

| Hits | Severity | Recommended stance |
|---|---|---|
| ≥1 csv_row | any | `REBUT-WITH-EVIDENCE` |
| only run_report or ledger | any | `REBUT-WITH-EVIDENCE` (point to the entry) |
| only literature_pool | any | `REBUT-WITH-EVIDENCE` (citation-style) |
| zero hits, severity=minor | minor | `CONCEDE-AND-PATCH` |
| zero hits, severity≥major | major / blocking | `NEW-EXPERIMENT-NEEDED` |
| atom matches a CFP exclusion regex | any | `OUT-OF-SCOPE` |

`OUT-OF-SCOPE` requires a verbatim quote from `stage0_setup/cfp.md` or
`venue_profile.yaml::avoid_patterns` in the evidence pointer, otherwise
the script downgrades it to `CONCEDE-AND-PATCH`.

## Evidence pointer format

```json
{
  "kind": "csv_row" | "run_report" | "claims_ledger" | "literature_pool" | "cfp",
  "path": "stage3_execution/results.csv",
  "row": 17,                       // for csv_row
  "section": "Deviations from plan", // for run_report
  "claim_id": "C-7",              // for claims_ledger
  "entry_id": "snell2024scaling", // for literature_pool
  "summary": "<≤120 char snippet>",
  "score": 0.42                   // cosine
}
```

A pointer with `score < 0.25` MUST NOT appear in `evidence_map.json`.
This is the bar that prevents "everything supports everything" rebuttals.

## Anti-patterns

* **Anchoring to unrun experiments.** If `evidence_map.json` references a
  csv row that doesn't exist, the orchestrator blocks the stage. Don't
  patch this around in `anchor_evidence.py`.
* **Citation reach.** If the only hit is a 0.27-cosine literature pool
  entry whose abstract barely mentions the topic, the recommended
  stance should still be `NEW-EXPERIMENT-NEEDED` — citations cannot
  rebut empirical-claim concerns.
