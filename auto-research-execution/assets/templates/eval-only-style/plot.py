#!/usr/bin/env python3
"""Render eval-only per-task / per-category accuracy bars.

Reads ``<results-dir>/results_summary.json`` shaped::

    {"<config>": {
        "accuracy": {"<task>": {"mean": 0.75, "std": 0.02}, ...}
    }, ...}

Tasks not present in every config are still plotted (missing → bar of
height 0 with a hatch). Best method per task is highlighted with a black
edge instead of a coloured edge — survives B/W printing.
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


def collect(summary: dict) -> tuple[list[str], list[str], np.ndarray, np.ndarray]:
    configs = sorted(summary)
    tasks: list[str] = []
    seen: set[str] = set()
    for config in configs:
        for task in summary[config].get("accuracy", {}):
            if task not in seen:
                seen.add(task)
                tasks.append(task)
    means = np.zeros((len(configs), len(tasks)))
    stds = np.zeros_like(means)
    for i, config in enumerate(configs):
        accuracy = summary[config].get("accuracy", {})
        for j, task in enumerate(tasks):
            entry = accuracy.get(task)
            if isinstance(entry, dict):
                means[i, j] = float(entry.get("mean", 0.0))
                stds[i, j] = float(entry.get("std", 0.0))
            elif entry is not None:
                means[i, j] = float(entry)
    return configs, tasks, means, stds


def plot_accuracy(summary: dict, out_path: pathlib.Path) -> bool:
    configs, tasks, means, stds = collect(summary)
    if not tasks:
        print("[plot] no per-task accuracy; skipping", file=sys.stderr)
        return False
    width = 0.8 / max(1, len(configs))
    fig, ax = plt.subplots(figsize=(max(3.5, 0.5 * len(tasks)), 2.5))
    best_idx_per_task = means.argmax(axis=0)
    for i, config in enumerate(configs):
        offsets = np.arange(len(tasks)) + (i - (len(configs) - 1) / 2.0) * width
        edge = ["black" if best_idx_per_task[j] == i else "none" for j in range(len(tasks))]
        ax.bar(offsets, means[i], yerr=stds[i], width=width, label=config,
               edgecolor=edge, linewidth=1.0, capsize=2)
    ax.set_xticks(range(len(tasks)), tasks, rotation=30, ha="right")
    ax.set_ylabel("Accuracy")
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
    plot_accuracy(load_summary(args.results_dir), args.out_dir / "accuracy_by_task.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
