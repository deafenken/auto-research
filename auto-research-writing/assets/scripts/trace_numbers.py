#!/usr/bin/env python3
"""Stage-4 number-provenance linter.

Every numeric literal in ``paper.tex`` (after stripping comments and
allowlisted patterns like section/figure refs) must trace to one of:

1. ``stage4_writing/claims_ledger.jsonl`` — agent-written ledger entry whose
   ``value`` matches and whose ``paper_tex_locator`` matches.
2. ``stage3_execution/results_summary.json`` — any mean/std field within
   ``--tolerance``.
3. ``stage3_execution/results.csv`` — any numeric cell within ``--tolerance``.
4. The abstract of a paper cited within ``--cite-proximity`` characters
   before the number (``stage1_ideation/literature_pool.json``).

Anything else is UNTRACED → exit 1 (or just a warning under ``--warn-only``).

The script is offline; it never hits the network. It's safe to run from a
pre-compile hook on a constrained VPS.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import re
import sys

from _lint_common import (
    Finding,
    LintReport,
    find_numbers,
    load_jsonl,
    strip_comments,
)


def _is_close(a: float, b: float, tolerance: float) -> bool:
    if a is None or b is None:
        return False
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=tolerance)


def search_summary(value: float, summary: dict, tolerance: float) -> str | None:
    """Return a dotted path to the matching key, else None."""
    def walk(node, path: str):
        if isinstance(node, dict):
            for k, v in node.items():
                hit = walk(v, f"{path}.{k}" if path else k)
                if hit:
                    return hit
        elif isinstance(node, list):
            for i, v in enumerate(node):
                hit = walk(v, f"{path}[{i}]")
                if hit:
                    return hit
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            if _is_close(float(node), value, tolerance):
                return path
        return None
    return walk(summary, "")


def search_csv(value: float, csv_path: pathlib.Path, tolerance: float) -> str | None:
    if not csv_path.is_file():
        return None
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            for col, raw in row.items():
                if raw is None:
                    continue
                try:
                    cell = float(raw)
                except (TypeError, ValueError):
                    continue
                if _is_close(cell, value, tolerance):
                    return f"row={i} col={col}"
    return None


def search_pool_abstract(value: float, keys: list[str], pool_by_key: dict,
                         tolerance: float) -> tuple[str, str] | None:
    """If any cited paper's abstract contains ``value`` (±tolerance), return
    (key, matched_token)."""
    if not keys:
        return None
    pattern = re.compile(r"[+-]?\d+(?:\.\d+)?")
    for key in keys:
        entry = pool_by_key.get(key)
        if not entry:
            continue
        abstract = entry.get("abstract") or ""
        for m in pattern.finditer(abstract):
            try:
                cited = float(m.group(0))
            except ValueError:
                continue
            if _is_close(cited, value, tolerance):
                return key, m.group(0)
    return None


def _index_pool(pool: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for entry in pool:
        for key in (entry.get("cite_key"), entry.get("bibtex_key"),
                    entry.get("s2_paper_id"), entry.get("arxiv_id"), entry.get("doi")):
            if key:
                out[str(key)] = entry
    return out


def _ledger_locator_match(num_locator: str, ledger_locator: str) -> bool:
    if not ledger_locator:
        return False
    if num_locator == ledger_locator:
        return True
    # Tolerate a shorter ledger locator (e.g. "paper.tex:L7" vs full
    # "paper.tex:L7:C12") by comparing the leading components.
    n_parts = num_locator.split(":")
    l_parts = ledger_locator.split(":")
    if 0 < len(l_parts) <= len(n_parts):
        return n_parts[: len(l_parts)] == l_parts
    return False


def search_ledger(value: float, locator: str, ledger: list[dict], tolerance: float) -> dict | None:
    for entry in ledger:
        try:
            ev = float(entry.get("value"))
        except (TypeError, ValueError):
            continue
        if not _is_close(ev, value, tolerance):
            continue
        if _ledger_locator_match(locator, entry.get("paper_tex_locator", "")):
            return entry
    return None


def run(report: LintReport, paper: pathlib.Path, run_dir: pathlib.Path,
        tolerance: float = 0.005, warn_only: bool = False) -> None:
    """Populate ``report`` with number-provenance findings. Caller writes."""
    if not paper.is_file():
        sys.exit(f"[trace_numbers] {paper} not found")
    raw_tex = paper.read_text()
    tex = strip_comments(raw_tex)
    numbers = find_numbers(tex)

    summary_path = run_dir / "stage3_execution" / "results_summary.json"
    csv_path = run_dir / "stage3_execution" / "results.csv"
    pool_path = run_dir / "stage1_ideation" / "literature_pool.json"
    ledger_path = paper.parent / "claims_ledger.jsonl"

    summary = {}
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text())
    pool: list[dict] = []
    if pool_path.is_file():
        pool_data = json.loads(pool_path.read_text())
        pool = pool_data if isinstance(pool_data, list) else pool_data.get("entries", [])
    pool_index = _index_pool(pool)
    ledger = load_jsonl(ledger_path)
    report.linters_run.append("trace_numbers.py")

    for num in numbers:
        # Priority 1: claims_ledger.
        led_entry = search_ledger(num.value, num.locator, ledger, tolerance)
        if led_entry:
            report.add_count("numbers", "VERIFIED")
            continue

        # Priority 2: results_summary.json.
        s_hit = search_summary(num.value, summary, tolerance)
        if s_hit:
            report.add_count("numbers", "VERIFIED")
            continue

        # Priority 3: results.csv.
        c_hit = search_csv(num.value, csv_path, tolerance)
        if c_hit:
            report.add_count("numbers", "VERIFIED")
            continue

        # Priority 4: prior-work via cited paper abstract.
        prior = search_pool_abstract(num.value, num.nearest_cite_keys,
                                       pool_index, tolerance)
        if prior:
            report.add_count("numbers", "VERIFIED-PRIOR-WORK")
            continue

        # Otherwise UNTRACED.
        severity = "warning" if warn_only else "error"
        report.add_count("numbers", "UNTRACED")
        report.add(Finding(
            rule="number-provenance",
            severity=severity,
            locator=num.locator,
            snippet=num.context,
            message=f"UNTRACED numeric literal `{num.raw}` (value={num.value})",
            extras={
                "kind": num.kind,
                "nearest_cite_keys": ",".join(num.nearest_cite_keys) or "(none)",
                "checked": "claims_ledger,results_summary,results.csv,cited-abstract",
            },
        ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", type=pathlib.Path, required=True)
    parser.add_argument("--run-dir", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, default=None)
    parser.add_argument("--tolerance", type=float, default=0.005)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    out_path = args.out or args.paper.parent / "lint_report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = LintReport(paper_path=args.paper, out_path=out_path)
    run(report, args.paper, args.run_dir,
        tolerance=args.tolerance, warn_only=args.warn_only)
    report.write()
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
