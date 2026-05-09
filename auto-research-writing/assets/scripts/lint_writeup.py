#!/usr/bin/env python3
"""Run both Stage-4 integrity linters and merge findings into one report.

Each linter populates a shared ``LintReport``; we write once. Exit code 1
if any linter found an error-severity violation; 0 otherwise.

Usage::

    python lint_writeup.py \\
        --paper runs/<id>/stage4_writing/paper.tex \\
        --run-dir runs/<id> \\
        --judge hybrid       # or none|mock|scicite|llm
"""
from __future__ import annotations

import argparse
import pathlib

import check_citations
import trace_numbers
from _lint_common import LintReport


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", type=pathlib.Path, required=True)
    parser.add_argument("--run-dir", type=pathlib.Path, required=True)
    parser.add_argument("--bib", type=pathlib.Path, default=None)
    parser.add_argument("--out", type=pathlib.Path, default=None)
    parser.add_argument("--judge", choices=["none", "mock", "scicite", "llm", "hybrid"],
                        default="hybrid")
    parser.add_argument("--judge-mock-file", type=pathlib.Path, default=None)
    parser.add_argument("--tolerance", type=float, default=0.005)
    parser.add_argument("--warn-only", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    out_path = args.out or args.paper.parent / "lint_report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = LintReport(paper_path=args.paper, out_path=out_path)

    check_citations.run(
        report, args.paper, args.run_dir,
        bib_path=args.bib, judge_name=args.judge,
        judge_mock_file=args.judge_mock_file,
        cache_dir=None if args.no_cache else pathlib.Path(".cache/citation_judge"),
        warn_only=args.warn_only,
    )
    trace_numbers.run(
        report, args.paper, args.run_dir,
        tolerance=args.tolerance, warn_only=args.warn_only,
    )

    report.write()
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
