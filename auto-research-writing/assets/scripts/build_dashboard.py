#!/usr/bin/env python3
"""Build the Inspector dashboard and stage it under ``runs/<id>/_dashboard/``.

The frontend lives at the repo top level (`auto-research-frontend/`). We
just shell out to ``npm run build`` (one-time) and copy the resulting
``dist/`` next to the run's artifacts, then symlink the artifacts the
SPA fetches via relative paths.

Usage::

    python build_dashboard.py --run-dir runs/<id>

User serves with::

    cd runs/<id>/_dashboard && python -m http.server 8000

Note: this script must be invoked from a machine that has Node + npm.
On the small auto-research VPS, generate the bundle elsewhere and rsync
the run dir over — the resulting `_dashboard/` is fully static.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys

# Walk parents until we find auto-research-frontend/. Works whether this
# script is invoked from the repo root or from inside a run dir.
def find_frontend_root(start: pathlib.Path) -> pathlib.Path:
    for parent in [start, *start.parents]:
        candidate = parent / "auto-research-frontend"
        if candidate.is_dir():
            return candidate
    sys.exit("[build_dashboard] could not locate auto-research-frontend/ above "
             f"{start}. Run from inside the repo or pass --frontend-dir.")


# Each (target_basename, source_relative_to_run_dir) pair. Only the first
# existing source becomes a symlink; missing ones are silently skipped.
ARTIFACT_MAP = (
    ("paper.tex",             "stage4_writing/paper.tex"),
    ("paper.pdf",             "stage4_writing/paper.pdf"),
    ("references.bib",        "stage4_writing/references.bib"),
    ("lint_report.md",        "stage4_writing/lint_report.md"),
    ("claims_ledger.jsonl",   "stage4_writing/claims_ledger.jsonl"),
    ("results.csv",           "stage3_execution/results.csv"),
    ("results_summary.json",  "stage3_execution/results_summary.json"),
    ("literature_pool.json",  "stage1_ideation/literature_pool.json"),
    ("run.yaml",              "run.yaml"),
)


def _link(target: pathlib.Path, source: pathlib.Path) -> None:
    if target.is_symlink() or target.exists():
        target.unlink()
    rel = os.path.relpath(source, start=target.parent)
    target.symlink_to(rel)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=pathlib.Path, required=True)
    parser.add_argument("--frontend-dir", type=pathlib.Path, default=None)
    parser.add_argument("--skip-build", action="store_true",
                        help="Use an existing dist/ instead of rebuilding")
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    if not run_dir.is_dir():
        sys.exit(f"[build_dashboard] {run_dir} is not a directory")
    frontend = (args.frontend_dir or find_frontend_root(pathlib.Path(__file__).resolve())).resolve()
    dist = frontend / "dist"

    if not args.skip_build:
        if not (frontend / "node_modules").is_dir():
            subprocess.run(["npm", "ci"], cwd=frontend, check=True)
        subprocess.run(["npm", "run", "build"], cwd=frontend, check=True)

    if not dist.is_dir():
        sys.exit(f"[build_dashboard] expected {dist} after build; nothing to copy")

    out_dir = run_dir / "_dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Copy the static bundle.
    for entry in dist.iterdir():
        target = out_dir / entry.name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        if entry.is_dir():
            shutil.copytree(entry, target)
        else:
            shutil.copy2(entry, target)

    # Stage run artifacts as siblings so `fetch('./paper.tex')` succeeds.
    for basename, rel in ARTIFACT_MAP:
        source = run_dir / rel
        if not source.exists():
            continue
        _link(out_dir / basename, source)

    print(f"[build_dashboard] Inspector ready at {out_dir}")
    print(f"[build_dashboard] serve with: cd {out_dir} && python -m http.server 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
