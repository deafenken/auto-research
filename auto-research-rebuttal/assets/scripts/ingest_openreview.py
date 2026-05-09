#!/usr/bin/env python3
"""Normalise reviewer comments into a single ``reviews_ingested.json``.

Two input modes:

* ``--input <dir>``: scan the directory for ``*.md`` (one reviewer per
  file) and ``*.json`` (forum-export format). Markdown is split via the
  heuristic in ``references/reviewer-axis-taxonomy.md``.
* ``--input <file>``: same logic on a single file.

When ``OPENREVIEW_USERNAME`` and ``OPENREVIEW_PASSWORD`` are set and the
input string starts with ``http`` / ``forum=``, we attempt to use
``openreview-py`` v2 to download the forum. The dependency is optional;
without it, paste the JSON manually.

The output schema is documented in ``../../SKILL.md`` Phase 1.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

AXIS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "soundness":   ("ablation", "ood", "doesn't generalise", "doesn't generalize",
                    "fails to", "no significance test", "no error bars",
                    "incorrect", "unsupported"),
    "clarity":     ("unclear", "hard to follow", "notation", "definition",
                    "ambiguous", "what is "),
    "novelty":     ("incremental", "very similar to", "already known",
                    "already done", "this just"),
    "significance": ("limited impact", "narrow", "real-world", "interesting if"),
    "presentation": ("typo", "figure", "table caption", "rephrase", "minor"),
}

SEVERITY_PATTERNS = (
    ("blocking", re.compile(r"\b(cannot accept|fundamental flaw|invalidates|reject)\b", re.I)),
    ("major",    re.compile(r"\b(would significantly|expect.{0,20}ablation|major|important)\b", re.I)),
    ("minor",    re.compile(r"\b(nit|typo|consider|small|would be nice|minor)\b", re.I)),
)


def classify(text: str) -> tuple[str, str]:
    lower = text.lower()
    axis = "soundness"  # safe default
    for cand, keywords in AXIS_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            axis = cand
            break
    severity = "major"  # default per axis taxonomy: prefer over-classification
    for sev, pattern in SEVERITY_PATTERNS:
        if pattern.search(text):
            severity = sev
            break
    return severity, axis


def split_markdown_into_atoms(text: str) -> list[str]:
    """Split a single review's markdown body into atomic comments.

    Strategy: respect bullet markers first, then fall back to sentence
    boundaries. Keep atoms ≥10 chars to avoid greeting-only fragments.
    """
    atoms: list[str] = []
    current: list[str] = []
    bullet_re = re.compile(r"^\s*[-*+]\s+|^\s*\d+\.\s+")
    for line in text.splitlines():
        if not line.strip():
            if current:
                atoms.extend(_finalize(" ".join(current)))
                current = []
            continue
        if bullet_re.match(line):
            if current:
                atoms.extend(_finalize(" ".join(current)))
                current = []
            current.append(bullet_re.sub("", line))
        else:
            current.append(line.strip())
    if current:
        atoms.extend(_finalize(" ".join(current)))
    return [a for a in atoms if len(a) >= 10]


def _finalize(text: str) -> list[str]:
    sentences = re.split(r"(?<=[\.!?])\s+(?=[A-Z\(\[])", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def normalise_review(review_id: str, role: str, body: str,
                      rating: int | None = None,
                      confidence: int | None = None) -> dict:
    atoms_text = split_markdown_into_atoms(body)
    atoms = []
    for i, atom in enumerate(atoms_text, start=1):
        severity, axis = classify(atom)
        atoms.append({
            "atom_id": f"R{review_id}.A{i}",
            "text": atom,
            "severity": severity,
            "axis": axis,
        })
    return {
        "review_id": f"R{review_id}",
        "reviewer_role": role,
        "rating": rating,
        "confidence": confidence,
        "comments": atoms,
    }


def from_markdown(path: pathlib.Path, review_index: int) -> dict:
    body = path.read_text()
    role = path.stem
    return normalise_review(str(review_index), role, body)


def from_openreview_json(blob: dict) -> list[dict]:
    """Best-effort parse of an OpenReview forum export."""
    out: list[dict] = []
    notes = blob.get("notes") or blob.get("review_notes") or []
    for i, note in enumerate(notes, start=1):
        content = note.get("content") or {}
        body_field = content.get("review") or content.get("comment") or content.get("text") or ""
        body = body_field.get("value") if isinstance(body_field, dict) else str(body_field)
        rating = _maybe_int(content.get("rating"))
        confidence = _maybe_int(content.get("confidence"))
        role = (note.get("signatures") or ["AnonymousReviewer"])[0]
        out.append(normalise_review(str(i), role, body, rating, confidence))
    return out


def _maybe_int(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("value")
    try:
        return int(str(value).split(":")[0])
    except (TypeError, ValueError):
        return None


def gather(input_path: pathlib.Path) -> list[dict]:
    reviews: list[dict] = []
    if input_path.is_dir():
        for i, path in enumerate(sorted(input_path.iterdir()), start=1):
            if path.suffix.lower() == ".md":
                reviews.append(from_markdown(path, i))
            elif path.suffix.lower() == ".json":
                blob = json.loads(path.read_text())
                reviews.extend(from_openreview_json(blob))
        return reviews
    if input_path.suffix.lower() == ".json":
        blob = json.loads(input_path.read_text())
        reviews.extend(from_openreview_json(blob))
        return reviews
    if input_path.suffix.lower() in (".md", ".txt"):
        reviews.append(from_markdown(input_path, 1))
        return reviews
    sys.exit(f"[ingest_openreview] cannot infer format for {input_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--paper-id", default=None)
    args = parser.parse_args()

    reviews = gather(args.input)
    payload = {
        "paper_id": args.paper_id or args.input.stem,
        "schema_version": 1,
        "reviews": reviews,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"[ingest_openreview] {sum(len(r['comments']) for r in reviews)} atoms across "
          f"{len(reviews)} reviews → {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
