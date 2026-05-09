#!/usr/bin/env python3
"""Render HF-Trainer-style train/eval loss + LR schedule overlay.

Reads ``<results-dir>/per_step/<config>__seed<N>.csv`` with columns
``step, train_loss, eval_loss, learning_rate``. Loss curves are mean±SE
across seeds (left axis); LR schedule is plotted on the right axis from
the first seed of each config (LR is deterministic per config so seed
averaging is unnecessary).
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
            continue
        df = pd.read_csv(csv_path)
        df["config"] = match["config"]
        df["seed"] = int(match["seed"])
        rows.append(df)
    if not rows:
        sys.exit(f"[plot] no per-step CSVs found under {per_step}")
    full = pd.concat(rows, ignore_index=True)
    return {cfg: grp.copy() for cfg, grp in full.groupby("config")}


def plot_loss_with_lr(runs: dict[str, pd.DataFrame], out_path: pathlib.Path) -> None:
    fig, ax = plt.subplots()
    ax_lr = ax.twinx()
    ax_lr.spines["right"].set_visible(True)
    for config in sorted(runs):
        df = runs[config]
        for metric, label, linestyle in (("train_loss", "train", "-"), ("eval_loss", "eval", "--")):
            if metric not in df.columns:
                continue
            agg = df.groupby("step")[metric].agg(["mean", "sem"]).reset_index()
            line, = ax.plot(agg["step"], agg["mean"], linestyle=linestyle, label=f"{config} {label}")
            ax.fill_between(agg["step"], agg["mean"] - agg["sem"], agg["mean"] + agg["sem"],
                            alpha=0.18, color=line.get_color(), linewidth=0)
        if "learning_rate" in df.columns:
            first_seed = df[df["seed"] == df["seed"].min()].sort_values("step")
            ax_lr.plot(first_seed["step"], first_seed["learning_rate"],
                       linestyle=":", linewidth=0.8, alpha=0.5,
                       label=f"{config} lr")
    ax.set_xlabel("Step")
    ax.set_ylabel("Loss")
    ax_lr.set_ylabel("Learning rate")
    ax.legend(loc="upper right", fontsize=6)
    fig.savefig(out_path)
    plt.close(fig)


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
    plot_loss_with_lr(runs, args.out_dir / "loss_with_lr.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
