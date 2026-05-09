#!/usr/bin/env python3
"""Launch a (config × seed) matrix with budget-awareness, resume, and per-run
failure isolation.

Upgrades over the v1 stub (closes contract gaps documented in
auto-research/references/integrity-rules.md Rule 5):

* **Budget tracker.** Sums ``gpu_hours`` from ``results.csv`` after each
  run and compares against ``run.yaml::budget.gpu_hours``. Warns at 50%,
  asks at 80%, hard-stops at 100%.
* **Resume.** Skips ``(config_name, seed)`` pairs already in
  ``results.csv`` whose ``git_commit`` matches the current commit. A
  changed commit re-runs (treated as a fresh experiment).
* **Progress.** Streams ``[i/N done] median-ETA T`` to stderr after
  each run. Median (not mean) protects ETA from a single slow seed.
* **Isolation.** Each run's stderr/stdout goes to its own log file so a
  late-run crash doesn't lose the earlier outputs. A failure is logged
  but does not stop subsequent runs unless ``--fail-fast`` is set.

The script remains stdlib-only — safe to ship into any execution
environment without depending on the heavier `auto-research-writing`
deps.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import statistics
import subprocess
import sys
import time
from typing import Iterable, Optional


# ---- helpers ---------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--command", required=True,
                        help="Base command, e.g. 'python train.py'")
    parser.add_argument("--configs", nargs="+", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--log-dir", default="../logs/stdout")
    parser.add_argument("--results-csv", default="../results.csv",
                        help="results.csv used for resume + budget tracking")
    parser.add_argument("--budget-gpu-hours", type=float, default=None,
                        help="Override run.yaml's budget for this invocation")
    parser.add_argument("--run-yaml", type=pathlib.Path, default=None,
                        help="Path to run.yaml; default: ../../run.yaml relative to log-dir")
    parser.add_argument("--fail-fast", action="store_true",
                        help="Stop the matrix on the first run failure (legacy v1 behaviour)")
    parser.add_argument("--ask-callback", default=None,
                        help="Path to a script that returns 'continue' or 'stop' "
                             "when budget hits 80%; default: prompt on TTY")
    parser.add_argument("--git-commit", default=None,
                        help="Override the auto-detected commit. Useful in CI / tests "
                             "where the working dir is not the experiment repo.")
    return parser.parse_args()


def iter_jobs(configs: Iterable[str], seeds: Iterable[int]) -> list[tuple[str, int]]:
    return [(c, s) for c in configs for s in seeds]


def current_git_commit(default: str = "unknown") -> str:
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True)
        return proc.stdout.strip()[:7] or default
    except (FileNotFoundError, subprocess.CalledProcessError):
        return default


def read_results_csv(path: pathlib.Path) -> tuple[list[dict], set[tuple[str, int, str]]]:
    """Return (rows, completed-set keyed by (config_name, seed, git_commit))."""
    if not path.is_file():
        return [], set()
    rows: list[dict] = []
    completed: set[tuple[str, int, str]] = set()
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
            try:
                seed = int(row["seed"]) if row.get("seed") not in (None, "") else None
            except ValueError:
                continue
            if seed is None or not row.get("config_name") or not row.get("git_commit"):
                continue
            completed.add((row["config_name"], seed, row["git_commit"]))
    return rows, completed


def parse_budget_from_run_yaml(path: pathlib.Path) -> Optional[float]:
    if not path.is_file():
        return None
    inside = False
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if line.startswith("budget:"):
            inside = True
            continue
        if inside:
            if line and not line.startswith((" ", "\t")):
                inside = False
                continue
            stripped = line.strip()
            if stripped.startswith("gpu_hours:"):
                _, _, value = stripped.partition(":")
                try:
                    return float(value.strip())
                except ValueError:
                    return None
    return None


def consumed_gpu_hours(rows: list[dict]) -> float:
    total = 0.0
    for row in rows:
        try:
            total += float(row.get("gpu_hours", 0) or 0)
        except (TypeError, ValueError):
            pass
    return total


def median_or(seconds: list[float], default: float) -> float:
    return statistics.median(seconds) if seconds else default


def emit(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def ask_continue(callback_path: Optional[str], remaining: float) -> bool:
    if callback_path and pathlib.Path(callback_path).is_file():
        proc = subprocess.run([callback_path, str(remaining)],
                              capture_output=True, text=True)
        return "continue" in (proc.stdout or "").lower()
    if not sys.stdin.isatty():
        emit("[launch_runs] non-interactive; defaulting to STOP at 80% budget")
        return False
    answer = input(f"[launch_runs] 80% budget reached, {remaining:.1f} GPU-h left. "
                    "Continue? [y/N] ").strip().lower()
    return answer.startswith("y")


# ---- main loop -------------------------------------------------------------


def run_one(cmd: list[str], env: dict, log_path: pathlib.Path) -> tuple[int, float]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write(f"$ {' '.join(cmd)}\n")
        handle.flush()
        proc = subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT, env=env)
    duration = time.monotonic() - start
    return proc.returncode, duration


def main() -> int:
    args = parse_args()
    log_dir = pathlib.Path(args.log_dir).resolve()
    results_csv = pathlib.Path(args.results_csv).resolve()
    run_yaml = (args.run_yaml or (log_dir / ".." / ".." / "run.yaml")).resolve()

    log_dir.mkdir(parents=True, exist_ok=True)

    git_commit = args.git_commit or current_git_commit()
    rows, completed = read_results_csv(results_csv)
    budget = args.budget_gpu_hours
    if budget is None:
        budget = parse_budget_from_run_yaml(run_yaml)

    jobs = iter_jobs(args.configs, args.seeds)
    todo: list[tuple[str, int]] = []
    skipped_resume = 0
    for config, seed in jobs:
        config_name = pathlib.Path(config).stem
        if (config_name, seed, git_commit) in completed:
            skipped_resume += 1
            continue
        todo.append((config, seed))

    total_planned = len(jobs)
    emit(f"[launch_runs] git_commit={git_commit} | planned={total_planned} | "
         f"resume-skip={skipped_resume} | todo={len(todo)} | "
         f"budget_gpu_hours={budget if budget is not None else 'unknown'}")

    durations: list[float] = []
    failures = 0
    consumed = consumed_gpu_hours(rows)
    warned_50 = consumed >= (budget or 0) * 0.5 if budget else False
    asked_80 = consumed >= (budget or 0) * 0.8 if budget else False

    for i, (config, seed) in enumerate(todo, start=1):
        if budget is not None and consumed >= budget:
            emit(f"[launch_runs] budget hard-stop at {consumed:.2f}/{budget:.2f} GPU-h")
            break

        config_name = pathlib.Path(config).stem
        run_name = f"{args.run_id}-{config_name}-seed{seed}"
        log_path = log_dir / f"{run_name}.log"
        env = os.environ.copy()
        env["RUN_ID"] = args.run_id
        env["CONFIG_NAME"] = config_name
        env["SEED"] = str(seed)
        env["GIT_COMMIT"] = git_commit
        cmd = args.command.split() + ["--config", config, "--seed", str(seed)]

        rc, dt = run_one(cmd, env, log_path)
        durations.append(dt)
        eta_seconds = median_or(durations, 0.0) * (len(todo) - i)
        if rc == 0:
            emit(f"[launch_runs] [{i}/{len(todo)}] OK   {run_name} "
                 f"({dt:.1f}s, ETA {eta_seconds:.0f}s)")
        else:
            failures += 1
            emit(f"[launch_runs] [{i}/{len(todo)}] FAIL {run_name} (rc={rc}) — see {log_path}")
            if args.fail_fast:
                emit("[launch_runs] --fail-fast set; aborting matrix")
                return rc

        # Re-read results.csv to update consumed (training script presumably
        # appended a row when it succeeded).
        rows, _completed = read_results_csv(results_csv)
        consumed = consumed_gpu_hours(rows)

        if budget:
            ratio = consumed / budget
            if not warned_50 and ratio >= 0.5:
                emit(f"[launch_runs] WARN 50% of budget consumed ({consumed:.2f}/{budget:.2f})")
                warned_50 = True
            if not asked_80 and ratio >= 0.8:
                asked_80 = True
                if not ask_continue(args.ask_callback, budget - consumed):
                    emit("[launch_runs] user declined to continue past 80% budget; stopping")
                    return 0

    emit(f"[launch_runs] done — {len(durations) - failures}/{len(durations)} succeeded, "
         f"{failures} failed; {consumed:.2f} GPU-h consumed of "
         f"{budget if budget is not None else '?'}")
    summary_path = log_dir / "launch_summary.json"
    summary_path.write_text(json.dumps({
        "git_commit": git_commit,
        "planned": total_planned,
        "skipped_resume": skipped_resume,
        "executed": len(durations),
        "failures": failures,
        "median_run_seconds": median_or(durations, 0.0),
        "consumed_gpu_hours": consumed,
        "budget_gpu_hours": budget,
    }, indent=2) + "\n")
    return 1 if failures and not args.fail_fast else 0


if __name__ == "__main__":
    raise SystemExit(main())
