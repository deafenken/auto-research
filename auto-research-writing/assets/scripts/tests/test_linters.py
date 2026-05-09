"""Tests for the Stage-4 integrity linters.

Runs against synthetic fixtures (no GPU, no network, no API keys). The
``mock`` judge keeps citation classification deterministic so the test
exercises the orchestration logic rather than any model.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
FIXTURES = TESTS / "fixtures"


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("LINT_FREEZE_TIME", "2026-05-09T00:00:00Z")
    env.setdefault("PYTHONPATH", f"{ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}")
    return subprocess.run(
        [sys.executable, str(ROOT / script), *args],
        capture_output=True, text=True, env=env,
    )


def _read_header(report_path: pathlib.Path) -> dict:
    text = report_path.read_text()
    head = text.split("-->", 1)[0]
    blob = head[head.find("{"):]
    return json.loads(blob)


class CleanRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_dir = FIXTURES / "clean_run"
        self.paper = self.run_dir / "stage4_writing" / "paper.tex"
        self.report = self.run_dir / "stage4_writing" / "lint_report.md"
        if self.report.exists():
            self.report.unlink()

    def test_lint_writeup_clean(self) -> None:
        proc = _run(
            "lint_writeup.py",
            "--paper", str(self.paper),
            "--run-dir", str(self.run_dir),
            "--judge", "mock",
            "--judge-mock-file", str(self.run_dir / "mock_judge.json"),
            "--no-cache",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        header = _read_header(self.report)
        self.assertEqual(header["exit_code"], 0)
        self.assertEqual(header["counts"].get("citations", {}).get("SUPPORTS"), 4)
        self.assertGreaterEqual(header["counts"].get("numbers", {}).get("VERIFIED", 0), 4)
        self.assertGreaterEqual(
            header["counts"].get("numbers", {}).get("VERIFIED-PRIOR-WORK", 0), 1)
        self.assertEqual(header["counts"].get("numbers", {}).get("UNTRACED", 0), 0)


class DirtyRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_dir = FIXTURES / "dirty_run"
        self.paper = self.run_dir / "stage4_writing" / "paper.tex"
        self.report = self.run_dir / "stage4_writing" / "lint_report.md"
        if self.report.exists():
            self.report.unlink()

    def test_lint_writeup_dirty_blocks(self) -> None:
        proc = _run(
            "lint_writeup.py",
            "--paper", str(self.paper),
            "--run-dir", str(self.run_dir),
            "--judge", "mock",
            "--judge-mock-file", str(self.run_dir / "mock_judge.json"),
            "--no-cache",
        )
        self.assertEqual(proc.returncode, 1, "expected dirty fixture to fail")
        body = self.report.read_text()
        self.assertIn("citation-bib-missing", body, body)
        self.assertIn("citation-relevance", body, body)
        self.assertIn("number-provenance", body, body)
        self.assertIn("ghost2099", body, body)
        self.assertIn("kingma2014adam", body, body)
        self.assertIn("99.9", body)
        self.assertIn("42.7", body)

    def test_lint_writeup_warn_only_passes(self) -> None:
        proc = _run(
            "lint_writeup.py",
            "--paper", str(self.paper),
            "--run-dir", str(self.run_dir),
            "--judge", "mock",
            "--judge-mock-file", str(self.run_dir / "mock_judge.json"),
            "--no-cache",
            "--warn-only",
        )
        self.assertEqual(proc.returncode, 0, "warn-only must downgrade errors")


class IdempotenceTests(unittest.TestCase):
    """Running the orchestrator twice on the same inputs must produce
    byte-identical reports (``LINT_FREEZE_TIME`` pins the timestamp)."""

    def test_byte_identical(self) -> None:
        run_dir = FIXTURES / "dirty_run"
        paper = run_dir / "stage4_writing" / "paper.tex"
        report = run_dir / "stage4_writing" / "lint_report.md"
        if report.exists():
            report.unlink()

        first = _run(
            "lint_writeup.py",
            "--paper", str(paper),
            "--run-dir", str(run_dir),
            "--judge", "mock",
            "--judge-mock-file", str(run_dir / "mock_judge.json"),
            "--no-cache",
        )
        body_a = report.read_bytes()

        second = _run(
            "lint_writeup.py",
            "--paper", str(paper),
            "--run-dir", str(run_dir),
            "--judge", "mock",
            "--judge-mock-file", str(run_dir / "mock_judge.json"),
            "--no-cache",
        )
        body_b = report.read_bytes()
        self.assertEqual(first.returncode, second.returncode)
        self.assertEqual(body_a, body_b)


if __name__ == "__main__":
    unittest.main()
