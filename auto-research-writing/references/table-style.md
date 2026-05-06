# Table Style

## Rules

1. One table, one claim.
2. Every table caption states the dataset, metric, and whether numbers are mean or mean ± std.
3. Bold only the best valid number per column.
4. Use `mean ± std` whenever multiple seeds were run.
5. If a baseline failed, mark it explicitly as `failed_to_run` or `n/a`, never leave the cell blank.

## Recommended main-results columns

- `Method`
- `Primary metric`
- `Key secondary metric`
- `GPU hours`

## Ablation table pattern

- `Variant`
- `Primary metric`
- `Delta vs full model`
- `Interpretation`

## Caption pattern

`Main results on <dataset>. Numbers are mean ± std over <N> seeds. Lower GPU hours are better only in the final column; all other metrics are higher-is-better unless noted.`
