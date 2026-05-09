#!/usr/bin/env python3
"""Render a venue-ready booktabs table from ``results_summary.json``.

Why programmatic: handing JSON numbers to an LLM for table formatting is a
fabrication vector (decimal slop, wrong-row bolding). This script keeps
formatting deterministic and lets the writer skill focus on prose.

Inputs
------
* ``results_summary.json`` — ``{config_name: {metric: {mean: float, std: float}}}``
  ``mean``/``std`` may also be plain floats (no std field).
* ``experiment_plan.yaml`` (optional) — used to read metric direction
  (``metrics.<name>.direction == 'min'|'max'``) and to pick the primary
  metric / column order.

Outputs
-------
* ``<out-dir>/main_results.tex`` — \\begin{tabular}…\\end{tabular} only.
  Wrap in \\begin{table}…\\end{table} in paper.tex.
* ``<out-dir>/table_metadata.json`` — which row was bolded per column,
  metric directions used, and the input file SHA256 for traceability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import sys
from typing import Any

try:
    import yaml  # PyYAML — already a transitive dep via existing skills.
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


def _load_summary(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        sys.exit(f"[render_table] {path} not found")
    return json.loads(path.read_text())


def _load_plan(path: pathlib.Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    if yaml is None:
        sys.exit("[render_table] PyYAML not installed; supply --metric-directions instead")
    return yaml.safe_load(path.read_text()) or {}


def _metric_directions(plan: dict[str, Any], cli: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    metrics = plan.get("metrics", {}) or {}
    if isinstance(metrics, dict):
        for name, body in metrics.items():
            if isinstance(body, dict) and "direction" in body:
                out[name] = body["direction"]
    out.update(cli)
    return out


def _format_cell(entry: Any, decimals: int) -> tuple[str, float | None]:
    if isinstance(entry, dict):
        mean = entry.get("mean")
        std = entry.get("std")
        if mean is None:
            return "--", None
        if std is None:
            return f"{float(mean):.{decimals}f}", float(mean)
        return f"{float(mean):.{decimals}f} $\\pm$ {float(std):.{decimals}f}", float(mean)
    if isinstance(entry, (int, float)) and not (isinstance(entry, float) and math.isnan(entry)):
        return f"{float(entry):.{decimals}f}", float(entry)
    return "--", None


def _winner(values: list[float | None], direction: str) -> int | None:
    indexed = [(i, v) for i, v in enumerate(values) if v is not None]
    if not indexed:
        return None
    if direction == "min":
        return min(indexed, key=lambda iv: iv[1])[0]
    return max(indexed, key=lambda iv: iv[1])[0]


def _columns(summary: dict[str, dict[str, Any]], plan: dict[str, Any]) -> list[str]:
    plan_metrics = plan.get("metrics") or {}
    primary = plan_metrics.get("primary") if isinstance(plan_metrics, dict) else None
    if isinstance(primary, str):
        primary_name = primary
    elif isinstance(primary, dict):
        primary_name = primary.get("name")
    else:
        primary_name = None

    seen: list[str] = []
    if primary_name:
        seen.append(primary_name)
    for cfg in summary.values():
        for metric in cfg:
            if metric not in seen:
                seen.append(metric)
    return seen


def render(summary: dict[str, dict[str, Any]],
           directions: dict[str, str],
           caption: str,
           label: str,
           decimals: int,
           default_direction: str,
           plan: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    rows = sorted(summary)
    cols = _columns(summary, plan)
    col_spec = "l" + "c" * len(cols)
    header = ["Method"] + [c.replace("_", " ") for c in cols]

    cell_text: list[list[str]] = []
    cell_value: list[list[float | None]] = []
    for row in rows:
        text_row, value_row = [], []
        for col in cols:
            text, value = _format_cell(summary[row].get(col), decimals)
            text_row.append(text)
            value_row.append(value)
        cell_text.append(text_row)
        cell_value.append(value_row)

    bolded_per_col: dict[str, str | None] = {}
    for j, col in enumerate(cols):
        direction = directions.get(col, default_direction)
        winner = _winner([row[j] for row in cell_value], direction)
        if winner is None:
            bolded_per_col[col] = None
            continue
        bolded_per_col[col] = rows[winner]
        cell_text[winner][j] = f"\\textbf{{{cell_text[winner][j]}}}"

    lines = [
        "\\begin{tabular}{" + col_spec + "}",
        "\\toprule",
        " & ".join(header) + " \\\\",
        "\\midrule",
    ]
    for row, text_row in zip(rows, cell_text):
        lines.append(row.replace("_", "\\_") + " & " + " & ".join(text_row) + " \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    if caption or label:
        lines.append(f"% caption: {caption}")
        lines.append(f"% label: {label}")
    tex = "\n".join(lines) + "\n"

    metadata = {
        "rows": rows,
        "columns": cols,
        "directions": {col: directions.get(col, default_direction) for col in cols},
        "bolded_per_column": bolded_per_col,
        "decimals": decimals,
        "caption": caption,
        "label": label,
    }
    return tex, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=pathlib.Path, required=True,
                        help="results_summary.json")
    parser.add_argument("--plan", type=pathlib.Path, default=None,
                        help="experiment_plan.yaml (optional, supplies metric directions)")
    parser.add_argument("--out-dir", type=pathlib.Path, required=True)
    parser.add_argument("--caption", default="Main results.")
    parser.add_argument("--label", default="tab:main")
    parser.add_argument("--decimals", type=int, default=2)
    parser.add_argument("--default-direction", choices=["max", "min"], default="max")
    parser.add_argument("--metric-direction", action="append", default=[],
                        metavar="METRIC=DIR",
                        help="Override per-metric direction, e.g. loss=min (repeatable).")
    args = parser.parse_args()

    cli_dirs: dict[str, str] = {}
    for entry in args.metric_direction:
        if "=" not in entry:
            sys.exit(f"--metric-direction expects METRIC=max|min, got {entry!r}")
        name, value = entry.split("=", 1)
        if value not in ("max", "min"):
            sys.exit(f"--metric-direction value must be max or min, got {value!r}")
        cli_dirs[name] = value

    summary = _load_summary(args.summary)
    plan = _load_plan(args.plan)
    directions = _metric_directions(plan, cli_dirs)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    tex, metadata = render(summary, directions, args.caption, args.label,
                           args.decimals, args.default_direction, plan)

    tex_path = args.out_dir / "main_results.tex"
    tex_path.write_text(tex)
    metadata["summary_sha256"] = hashlib.sha256(args.summary.read_bytes()).hexdigest()
    (args.out_dir / "table_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"[render_table] wrote {tex_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
