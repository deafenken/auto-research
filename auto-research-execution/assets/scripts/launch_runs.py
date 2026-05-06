#!/usr/bin/env python3
"""Launch a matrix of config/seed runs with simple stdout logging."""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--command", required=True, help="Base command, e.g. `python train.py`.")
    parser.add_argument("--configs", nargs="+", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--log-dir", default="../logs/stdout")
    return parser.parse_args()


def iter_jobs(configs: Iterable[str], seeds: Iterable[int]) -> Iterable[tuple[str, int]]:
    for config in configs:
        for seed in seeds:
            yield config, seed


def main() -> int:
    args = parse_args()
    log_dir = pathlib.Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    for config, seed in iter_jobs(args.configs, args.seeds):
        run_name = f"{args.run_id}-{pathlib.Path(config).stem}-seed{seed}"
        log_path = log_dir / f"{run_name}.log"
        env = os.environ.copy()
        env["RUN_ID"] = args.run_id
        env["CONFIG_NAME"] = pathlib.Path(config).stem
        env["SEED"] = str(seed)
        cmd = args.command.split() + ["--config", config, "--seed", str(seed)]

        with log_path.open("w", encoding="utf-8") as handle:
            handle.write(f"$ {' '.join(cmd)}\n")
            handle.flush()
            proc = subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT, env=env)

        if proc.returncode != 0:
            print(f"[launch_runs] failed: {run_name} -> {log_path}", file=sys.stderr)
            return proc.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
