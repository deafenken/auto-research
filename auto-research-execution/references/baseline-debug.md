# Baseline Debug

Use this when a planned baseline does not reproduce.

## Protocol

1. Confirm dataset, split, metric, and preprocessing match the paper.
2. Confirm checkpoint or initialization matches the claimed setup.
3. Compare your config to the baseline paper line-by-line.
4. Run a short smoke test before a full reproduction.
5. Log every mismatch in `run_report.md`.

## Tolerance

- A baseline is considered reproduced only if it lands within `±20%` of the expected metric gap or absolute metric declared in `experiment_plan.yaml`.
- If the paper reports a range, target the midpoint and justify deviation.

## Escalate when

- The official code is unavailable or broken beyond 5 repair attempts.
- The paper omits critical hyperparameters.
- Reproducing the baseline would break the run budget.

Never replace the baseline with a weaker one without surfacing the change.
