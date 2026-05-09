#!/usr/bin/env python3
"""Render nanoGPT-style training curves with mean±SE bands across seeds.

Reads per-step metric CSVs at ``<results-dir>/per_step/<config>__seed<N>.csv``
with columns ``step, train_loss, val_loss, val_perplexity`` (extra columns
are ignored). Emits ``train_loss.png`` and ``val_perplexity.png`` under
``<out-dir>``. Use the shared venue mplstyle for camera-ready fonts.

Synthetic-fixture friendly: missing columns produce a one-line warning and
the figure for that metric is skipped instead of crashing.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import matplotlib.pyplot as plt
import pandas as pd

STYLE_PATH = pathlib.Path(__file__).resolve().parents[2] / "styles" / "venue_style.mplstyle"
RUN_RE = re.compile(r"^(?P<config>.+)__seed(?P<seed>\d+)\.csv$")


def load_per_step(results_dir: pathlib.Path) -> dict[str, pd.DataFrame]:
    per_step = results_dir / "per_step"
    if not per_step.is_dir():
        sys.exit(f"[plot] expected directory {per_step} not found")
    rows: list[pd.DataFrame] = []
    for csv_path in sorted(per_step.glob("*.csv")):
        match = RUN_RE.match(csv_path.name)
        if not match:
            print(f"[plot] skipping unrecognised file {csv_path.name}", file=sys.stderr)
            continue
        df = pd.read_csv(csv_path)
        df["config"] = match["config"]
        df["seed"] = int(match["seed"])
        rows.append(df)
    if not rows:
        sys.exit(f"[plot] no per-step CSVs found under {per_step}")
    full = pd.concat(rows, ignore_index=True)
    return {cfg: grp.copy() for cfg, grp in full.groupby("config")}


def plot_metric(runs: dict[str, pd.DataFrame], metric: str, ylabel: str, out_path: pathlib.Path) -> bool:
    fig, ax = plt.subplots()
    plotted = False
    for config in sorted(runs):
        df = runs[config]
        if metric not in df.columns:
            continue
        agg = df.groupby("step")[metric].agg(["mean", "sem"]).reset_index()
        ax.plot(agg["step"], agg["mean"], label=config)
        ax.fill_between(agg["step"], agg["mean"] - agg["sem"], agg["mean"] + agg["sem"], alpha=0.2, linewidth=0)
        plotted = True
    if not plotted:
        plt.close(fig)
        print(f"[plot] metric '{metric}' missing in all runs, skipping {out_path.name}", file=sys.stderr)
        return False
    ax.set_xlabel("Training step")
    ax.set_ylabel(ylabel)
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

    runs = load_per_step(args.results_dir)
    plot_metric(runs, "train_loss", "Train loss", args.out_dir / "train_loss.png")
    if not plot_metric(runs, "val_perplexity", "Val perplexity", args.out_dir / "val_perplexity.png"):
        plot_metric(runs, "val_loss", "Val loss", args.out_dir / "val_loss.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
