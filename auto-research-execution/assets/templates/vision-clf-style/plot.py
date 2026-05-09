#!/usr/bin/env python3
"""Render vision-classification confusion matrix + per-class F1 bars.

Expects ``<results-dir>/results_summary.json`` shaped::

    {"<config>": {
        "accuracy": 0.92,
        "per_class_f1": {"airplane": 0.89, ...},
        "confusion_matrix": [[950, 20, ...], ...],
        "class_names": ["airplane", ...]
    }, ...}

For multi-config runs, the lexicographically first config drives the
confusion-matrix figure; per-class F1 bars are grouped across configs.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import matplotlib.pyplot as plt
import numpy as np

STYLE_PATH = pathlib.Path(__file__).resolve().parents[2] / "styles" / "venue_style.mplstyle"


def load_summary(results_dir: pathlib.Path) -> dict:
    summary_path = results_dir / "results_summary.json"
    if not summary_path.is_file():
        sys.exit(f"[plot] {summary_path} not found")
    return json.loads(summary_path.read_text())


def plot_confusion(summary: dict, out_path: pathlib.Path) -> bool:
    config = sorted(summary)[0]
    entry = summary[config]
    cm = np.asarray(entry.get("confusion_matrix", []), dtype=float)
    if cm.size == 0:
        print("[plot] no confusion_matrix in summary; skipping", file=sys.stderr)
        return False
    row_sum = cm.sum(axis=1, keepdims=True)
    norm = np.divide(cm, row_sum, out=np.zeros_like(cm), where=row_sum > 0)
    classes = entry.get("class_names") or [str(i) for i in range(cm.shape[0])]

    fig, ax = plt.subplots(figsize=(3.5, 3.0))
    im = ax.imshow(norm, cmap="Blues", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(classes)), classes, rotation=45, ha="right")
    ax.set_yticks(range(len(classes)), classes)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix — {config}")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.savefig(out_path)
    plt.close(fig)
    return True


def plot_per_class_f1(summary: dict, out_path: pathlib.Path) -> bool:
    configs = sorted(summary)
    f1_tables = [(c, summary[c].get("per_class_f1", {})) for c in configs]
    f1_tables = [(c, t) for c, t in f1_tables if t]
    if not f1_tables:
        print("[plot] no per_class_f1 in summary; skipping", file=sys.stderr)
        return False
    classes = list(f1_tables[0][1].keys())
    width = 0.8 / max(1, len(f1_tables))
    fig, ax = plt.subplots(figsize=(max(3.5, 0.45 * len(classes)), 2.5))
    for i, (config, table) in enumerate(f1_tables):
        offsets = np.arange(len(classes)) + (i - (len(f1_tables) - 1) / 2.0) * width
        ax.bar(offsets, [table.get(c, 0.0) for c in classes], width=width, label=config)
    ax.set_xticks(range(len(classes)), classes, rotation=45, ha="right")
    ax.set_ylabel("F1")
    ax.set_ylim(0.0, 1.0)
    ax.legend()
    fig.savefig(out_path)
    plt.close(fig)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=pathlib.Path, required=True)
    parser.add_argument("--out-dir", type=pathlib.Path, required=True)
    parser.add_argument("--style", type=pathlib.Path, default=STYLE_PATH)
    args = parser.parse_args()

    if args.style.is_file():
        plt.style.use(str(args.style))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = load_summary(args.results_dir)
    plot_confusion(summary, args.out_dir / "confusion_matrix.png")
    plot_per_class_f1(summary, args.out_dir / "per_class_f1.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
