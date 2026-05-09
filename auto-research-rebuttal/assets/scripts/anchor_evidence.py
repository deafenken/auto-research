#!/usr/bin/env python3
"""Anchor each reviewer atom to artifacts already on disk.

Implements the priority-ordered TF-IDF search from
``references/evidence-anchoring.md`` and emits a recommended stance
per atom. Pure Python; no sklearn / scipy dependency.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import re
import sys
from collections import Counter

THRESHOLD = 0.25
TOP_K_PER_SOURCE = 3
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
STOPWORDS = frozenset({
    "the","a","an","is","are","of","to","in","on","by","for","and","or","but",
    "we","our","this","that","these","those","it","its","be","been","with",
    "at","as","from","into","than","then","do","does","did","not","no","can",
    "could","would","should","also","such","may","might","will","i","you",
})


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")
            if t.lower() not in STOPWORDS and len(t) > 1]


def tf(tokens: list[str]) -> Counter[str]:
    return Counter(tokens)


def idf(docs: list[list[str]]) -> dict[str, float]:
    N = max(1, len(docs))
    df: Counter[str] = Counter()
    for doc in docs:
        for term in set(doc):
            df[term] += 1
    return {t: math.log((N + 1) / (1 + n)) + 1.0 for t, n in df.items()}


def vec(tokens: list[str], idf_map: dict[str, float]) -> dict[str, float]:
    counts = tf(tokens)
    return {t: c * idf_map.get(t, 0.0) for t, c in counts.items()}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    num = sum(a[t] * b[t] for t in a if t in b)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


# ---- Source loaders --------------------------------------------------------


def load_csv_rows(path: pathlib.Path) -> list[tuple[str, dict]]:
    if not path.is_file():
        return []
    out: list[tuple[str, dict]] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            doc = " ".join(f"{k}={v}" for k, v in row.items() if v not in (None, ""))
            out.append((doc, {"row": i, **row}))
    return out


def load_run_report(path: pathlib.Path) -> list[tuple[str, dict]]:
    if not path.is_file():
        return []
    text = path.read_text()
    sections: list[tuple[str, dict]] = []
    current_title = "(preamble)"
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append((
                    " ".join(current_lines),
                    {"section": current_title}))
                current_lines = []
            current_title = line[3:].strip()
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((" ".join(current_lines), {"section": current_title}))
    return sections


def load_ledger(path: pathlib.Path) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    if not path.is_file():
        return out
    for raw in path.read_text().splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        doc = " ".join(str(entry.get(k, "")) for k in (
            "metric", "unit", "source", "config_name", "paper_tex_locator"))
        out.append((doc, entry))
    return out


def load_pool(path: pathlib.Path) -> list[tuple[str, dict]]:
    if not path.is_file():
        return []
    blob = json.loads(path.read_text())
    if isinstance(blob, dict):
        blob = blob.get("entries", [])
    out: list[tuple[str, dict]] = []
    for entry in blob or []:
        doc = " ".join((entry.get("title") or "",
                         entry.get("abstract") or ""))
        out.append((doc, entry))
    return out


def load_cfp(run_dir: pathlib.Path) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    cfp_path = run_dir / "stage0_setup" / "cfp.md"
    if cfp_path.is_file():
        out.append((cfp_path.read_text(),
                    {"path": str(cfp_path.relative_to(run_dir))}))
    venue_path = run_dir / "stage0_setup" / "venue_profile.yaml"
    if venue_path.is_file():
        out.append((venue_path.read_text(),
                    {"path": str(venue_path.relative_to(run_dir))}))
    return out


# ---- Search & stance ------------------------------------------------------


def search(atom_tokens: list[str], docs: list[tuple[str, dict]],
           kind: str, run_dir: pathlib.Path) -> list[dict]:
    if not docs:
        return []
    tokenised = [tokenize(d[0]) for d in docs]
    idf_map = idf(tokenised)
    atom_vec = vec(atom_tokens, idf_map)
    scored: list[tuple[float, int]] = []
    for i, doc_tokens in enumerate(tokenised):
        s = cosine(atom_vec, vec(doc_tokens, idf_map))
        if s >= THRESHOLD:
            scored.append((s, i))
    scored.sort(reverse=True)
    out: list[dict] = []
    for score, idx in scored[:TOP_K_PER_SOURCE]:
        text, meta = docs[idx]
        snippet = " ".join(text.split())[:120]
        ptr: dict = {"kind": kind, "summary": snippet, "score": round(score, 3)}
        if kind == "csv_row":
            ptr["path"] = "stage3_execution/results.csv"
            ptr["row"] = meta["row"]
        elif kind == "run_report":
            ptr["path"] = "stage3_execution/run_report.md"
            ptr["section"] = meta["section"]
        elif kind == "claims_ledger":
            ptr["path"] = "stage4_writing/claims_ledger.jsonl"
            ptr["claim_id"] = meta.get("claim_id")
        elif kind == "literature_pool":
            ptr["path"] = "stage1_ideation/literature_pool.json"
            ptr["entry_id"] = (meta.get("cite_key") or meta.get("bibtex_key")
                                or meta.get("s2_paper_id") or meta.get("arxiv_id"))
        elif kind == "cfp":
            ptr["path"] = meta.get("path", "stage0_setup/cfp.md")
        del run_dir  # unused; kept for symmetry / future expansion
        out.append(ptr)
    return out


def recommend_stance(atom: dict, evidence: list[dict],
                       cfp_text: str) -> str:
    if any(e["kind"] == "csv_row" for e in evidence):
        return "REBUT-WITH-EVIDENCE"
    if cfp_text and _matches_exclusion(atom["text"], cfp_text):
        return "OUT-OF-SCOPE"
    if any(e["kind"] in ("run_report", "claims_ledger", "literature_pool") for e in evidence):
        return "REBUT-WITH-EVIDENCE"
    if atom["severity"] == "minor":
        return "CONCEDE-AND-PATCH"
    return "NEW-EXPERIMENT-NEEDED"


def _matches_exclusion(atom_text: str, cfp_text: str) -> bool:
    """Crude: any line in cfp.md that starts with 'avoid' / 'out of scope'
    and shares ≥3 tokens with the atom flips the stance."""
    atom_tokens = set(tokenize(atom_text))
    if not atom_tokens:
        return False
    for line in cfp_text.splitlines():
        lower = line.strip().lower()
        if not lower.startswith(("avoid", "out of scope", "scope:")):
            continue
        if len(atom_tokens & set(tokenize(line))) >= 3:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=pathlib.Path, required=True)
    parser.add_argument("--run-dir", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    reviews_blob = json.loads(args.reviews.read_text())
    csv_docs = load_csv_rows(args.run_dir / "stage3_execution" / "results.csv")
    report_docs = load_run_report(args.run_dir / "stage3_execution" / "run_report.md")
    ledger_docs = load_ledger(args.run_dir / "stage4_writing" / "claims_ledger.jsonl")
    pool_docs = load_pool(args.run_dir / "stage1_ideation" / "literature_pool.json")
    cfp_docs = load_cfp(args.run_dir)
    cfp_text = "\n".join(d[0] for d in cfp_docs)

    out: dict[str, dict] = {}
    for review in reviews_blob.get("reviews", []):
        for atom in review.get("comments", []):
            atom_tokens = tokenize(atom["text"])
            evidence: list[dict] = []
            evidence.extend(search(atom_tokens, csv_docs, "csv_row", args.run_dir))
            evidence.extend(search(atom_tokens, report_docs, "run_report", args.run_dir))
            evidence.extend(search(atom_tokens, ledger_docs, "claims_ledger", args.run_dir))
            evidence.extend(search(atom_tokens, pool_docs, "literature_pool", args.run_dir))
            stance = recommend_stance(atom, evidence, cfp_text)
            evidence_strength = max((e["score"] for e in evidence), default=0.0)
            out[atom["atom_id"]] = {
                "stance_recommended": stance,
                "evidence_strength": round(evidence_strength, 3),
                "evidence": evidence,
                "axis": atom.get("axis"),
                "severity": atom.get("severity"),
            }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(f"[anchor_evidence] {len(out)} atoms anchored → {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
