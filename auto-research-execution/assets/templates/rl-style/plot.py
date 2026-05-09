#!/usr/bin/env python3
"""Render RL episode-return curve with confidence band + sample efficiency.

Reads ``<results-dir>/per_step/<config>__seed<N>.csv`` with columns
``env_steps, episode_return, wall_time_sec`` (extra columns ignored).
Produces:

* ``episode_return.png`` — mean return ± SE band vs. environment steps.
* ``sample_efficiency.png`` — area under the mean-return curve normalized
  by total wall-time, plotted as a bar per config (higher is better).

Smoothing default is a 10-episode rolling median; pass ``--no-smooth`` to
disable. Median (not mean) protects against single-episode return spikes.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
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


def plot_returns(runs: dict[str, pd.DataFrame], out_path: pathlib.Path, smooth: int) -> None:
    fig, ax = plt.subplots()
    for config in sorted(runs):
        df = runs[config]
        if "env_steps" not in df.columns or "episode_return" not in df.columns:
            continue
        if smooth > 1:
            df = df.copy()
            df["episode_return"] = df.groupby("seed")["episode_return"].transform(
                lambda s: s.rolling(smooth, min_periods=1).median()
            )
        agg = df.groupby("env_steps")["episode_return"].agg(["mean", "sem"]).reset_index()
        line, = ax.plot(agg["env_steps"], agg["mean"], label=config)
        ax.fill_between(agg["env_steps"], agg["mean"] - agg["sem"], agg["mean"] + agg["sem"],
                        alpha=0.2, color=line.get_color(), linewidth=0)
    ax.set_xlabel("Environment steps")
    ax.set_ylabel("Episode return")
    ax.legend()
    fig.savefig(out_path)
    plt.close(fig)


def plot_sample_efficiency(runs: dict[str, pd.DataFrame], out_path: pathlib.Path) -> bool:
    scores: dict[str, float] = {}
    for config, df in runs.items():
        if "wall_time_sec" not in df.columns or "episode_return" not in df.columns:
            continue
        per_seed = []
        for _, sdf in df.groupby("seed"):
            sdf = sdf.sort_values("env_steps")
            wall = max(sdf["wall_time_sec"].max(), 1e-6)
            per_seed.append(np.trapezoid(sdf["episode_return"], sdf["env_steps"]) / wall)
        if per_seed:
            scores[config] = float(np.mean(per_seed))
    if not scores:
        print("[plot] missing wall_time_sec; skipping sample_efficiency", file=sys.stderr)
        return False
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    configs = sorted(scores)
    ax.bar(configs, [scores[c] for c in configs])
    ax.set_ylabel("Return-AUC / wall-time")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.savefig(out_path)
    plt.close(fig)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=pathlib.Path, required=True)
    parser.add_argument("--out-dir", type=pathlib.Path, required=True)
    parser.add_argument("--style", type=pathlib.Path, default=STYLE_PATH)
    parser.add_argument("--smooth", type=int, default=10, help="rolling-median window in episodes")
    parser.add_argument("--no-smooth", action="store_true")
    args = parser.parse_args()

    if args.style.is_file():
        plt.style.use(str(args.style))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    runs = load_per_step(args.results_dir)
    plot_returns(runs, args.out_dir / "episode_return.png", smooth=1 if args.no_smooth else args.smooth)
    plot_sample_efficiency(runs, args.out_dir / "sample_efficiency.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
