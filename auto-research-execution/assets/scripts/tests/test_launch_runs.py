"""Tests for launch_runs.py upgrades (R6).

Synthetic only — no GPU, no real training. The "training script" is a tiny
stub that appends a row to results.csv with a configurable gpu_hours / rc,
which is exactly what real training scripts are expected to do.
"""
from __future__ import annotations

import csv
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS = pathlib.Path(__file__).resolve().parent
FIXTURES = TESTS / "fixtures"


STUB_TRAINER = textwrap.dedent("""
    #!/usr/bin/env python3
    import argparse, csv, os, pathlib, sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--results-csv", required=True)
    parser.add_argument("--gpu-hours", type=float, default=0.5)
    parser.add_argument("--rc", type=int, default=0)
    parser.add_argument("--event-flag", default="clean")
    args = parser.parse_args()

    if args.rc != 0:
        sys.exit(args.rc)

    config_name = pathlib.Path(args.config).stem
    git_commit = os.environ.get("GIT_COMMIT", "unknown")
    csv_path = pathlib.Path(args.results_csv)
    new_file = not csv_path.is_file()
    with csv_path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(["run_id", "config_name", "seed", "git_commit",
                             "gpu_hours", "primary_metric", "event_flags", "notes"])
        writer.writerow([
            os.environ.get("RUN_ID", "test"), config_name, args.seed, git_commit,
            args.gpu_hours, 0.5, args.event_flag, ""
        ])
""")


class LauncherFixture:
    """Per-test sandbox that hosts run.yaml, results.csv, and a stub trainer."""

    def __init__(self) -> None:
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="launch_runs_test_"))
        self.code = self.tmp / "code"
        self.code.mkdir()
        self.stage = self.tmp / "stage3_execution"
        self.stage.mkdir()
        (self.stage / "logs" / "stdout").mkdir(parents=True)
        # run.yaml lives at runs/<id>/run.yaml — we mirror that here.
        shutil.copy(FIXTURES / "run.yaml", self.tmp / "run.yaml")
        self.results_csv = self.stage / "results.csv"
        self.trainer = self.code / "train.py"
        self.trainer.write_text(STUB_TRAINER)
        os.chmod(self.trainer, 0o755)
        for cfg in ("baseline_chinchilla.yaml", "ours_method.yaml"):
            (self.code / cfg).write_text("dummy: true\n")

    def cleanup(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def launch(self, *extra: str, gpu_hours: float = 0.5,
               rc: int = 0, env_overrides: dict | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
        # GIT_COMMIT pinned so resume tests are deterministic without a git repo.
        commit = env.setdefault("GIT_COMMIT", "abc1234")
        cmd = [
            sys.executable, str(ROOT / "launch_runs.py"),
            "--run-id", "fixture",
            "--command", f"{sys.executable} {self.trainer} "
                          f"--results-csv {self.results_csv} "
                          f"--gpu-hours {gpu_hours} --rc {rc}",
            "--configs",
            str(self.code / "baseline_chinchilla.yaml"),
            str(self.code / "ours_method.yaml"),
            "--seeds", "13", "42",
            "--log-dir", str(self.stage / "logs" / "stdout"),
            "--results-csv", str(self.results_csv),
            "--run-yaml", str(self.tmp / "run.yaml"),
            "--git-commit", commit,
            *extra,
        ]
        return subprocess.run(cmd, capture_output=True, text=True, env=env)


class ResumeTests(unittest.TestCase):
    def test_skips_completed_pairs(self) -> None:
        fx = LauncherFixture()
        try:
            shutil.copy(FIXTURES / "synthetic_results.csv", fx.results_csv)
            proc = fx.launch(gpu_hours=0.5)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("resume-skip=4", proc.stderr)
            self.assertIn("todo=0", proc.stderr)
        finally:
            fx.cleanup()

    def test_runs_when_commit_changes(self) -> None:
        fx = LauncherFixture()
        try:
            shutil.copy(FIXTURES / "synthetic_results.csv", fx.results_csv)
            proc = fx.launch(gpu_hours=0.4,
                             env_overrides={"GIT_COMMIT": "deadbee"})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("resume-skip=0", proc.stderr)
            self.assertIn("todo=4", proc.stderr)
        finally:
            fx.cleanup()


class BudgetTests(unittest.TestCase):
    def test_warns_at_50_percent(self) -> None:
        fx = LauncherFixture()
        try:
            # Budget is 3.0 GPU-h. Each run takes 0.8 GPU-h → after 2 runs we hit
            # 1.6 GPU-h (>50%) but stay below 80% (2.4 GPU-h).
            proc = fx.launch(gpu_hours=0.8,
                             env_overrides={"GIT_COMMIT": "newcomm"})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("WARN 50%", proc.stderr)
        finally:
            fx.cleanup()

    def test_hard_stops_at_100_percent(self) -> None:
        fx = LauncherFixture()
        try:
            # 4 runs at 1.0 GPU-h each = 4.0 GPU-h vs budget 3.0 → hard-stop.
            # Use --ask-callback that says continue so 80% doesn't intercept.
            cb = fx.tmp / "always_continue.sh"
            cb.write_text("#!/bin/sh\necho continue\n")
            os.chmod(cb, 0o755)
            proc = fx.launch("--ask-callback", str(cb),
                             gpu_hours=1.0,
                             env_overrides={"GIT_COMMIT": "budgcom"})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("budget hard-stop", proc.stderr)
            with fx.results_csv.open() as fh:
                rows = list(csv.DictReader(fh))
            # We should have stopped before completing all 4 runs.
            self.assertLess(len(rows), 4, rows)
        finally:
            fx.cleanup()

    def test_eighty_percent_callback_can_stop(self) -> None:
        fx = LauncherFixture()
        try:
            cb = fx.tmp / "always_stop.sh"
            cb.write_text("#!/bin/sh\necho stop\n")
            os.chmod(cb, 0o755)
            proc = fx.launch("--ask-callback", str(cb),
                             gpu_hours=0.9,
                             env_overrides={"GIT_COMMIT": "stopcom"})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("declined to continue past 80%", proc.stderr)
        finally:
            fx.cleanup()


class IsolationTests(unittest.TestCase):
    def test_one_failure_does_not_stop_others(self) -> None:
        fx = LauncherFixture()
        try:
            # Run with rc=1 for ALL — by default we keep going and exit 1 at the end.
            proc = fx.launch(rc=1, gpu_hours=0.1,
                             env_overrides={"GIT_COMMIT": "failcom"})
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertEqual(proc.stderr.count("FAIL"), 4)
        finally:
            fx.cleanup()

    def test_fail_fast_stops_on_first_error(self) -> None:
        fx = LauncherFixture()
        try:
            proc = fx.launch("--fail-fast", rc=2, gpu_hours=0.1,
                             env_overrides={"GIT_COMMIT": "ffcom"})
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertEqual(proc.stderr.count("FAIL"), 1)
        finally:
            fx.cleanup()


if __name__ == "__main__":
    unittest.main()
