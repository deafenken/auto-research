# WandB Conventions

Use a stable naming scheme so runs can be aggregated without guessing.

## Required config fields

- `run_id`
- `config_name`
- `seed`
- `git_commit`
- `hardware`
- `planned_gpu_hours`

## Required metrics

- training loss
- validation metric(s)
- wall-clock time
- estimated GPU hours consumed

## Naming

- Project: `auto-research`
- Run name: `<run_id>/<config_name>/seed-<seed>`
- Tags: domain, template, baseline-or-method, stage3

If WandB is unavailable, mirror the same fields to TensorBoard or JSON logs.
