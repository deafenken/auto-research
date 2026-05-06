#!/usr/bin/env python3
"""
Verify citations through the 4-layer protocol described in
references/citation-verification.md.

Usage:
    python citation_verify.py --input candidates.json --output candidates_verified.json

The input is a JSON list of citation candidates, each with at least one of:
    {"doi": "...", "arxiv_id": "...", "s2_paper_id": "...", "title": "...",
     "first_author_lastname": "...", "year": 2024}

The output adds either:
    "verified_via": ["arxiv:200ok", "crossref:match", "s2_triangulate:match"]
or
    "verification_failed": "<which_layer>_<short_reason>"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests


S2_BASE = "https://api.semanticscholar.org/graph/v1"
ARXIV_BASE = "https://arxiv.org/abs"
DOI_BASE = "https://doi.org"
CROSSREF_BASE = "https://api.crossref.org/works"

S2_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
DEFAULT_TIMEOUT = 15
RETRY_BACKOFF = (5, 15, 45)


def _s2_headers() -> dict:
    return {"x-api-key": S2_API_KEY} if S2_API_KEY else {}


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def title_overlap(a: str, b: str) -> float:
    """Word-set overlap between two titles after normalization."""
    aw = set(normalize_title(a).split())
    bw = set(normalize_title(b).split())
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / max(len(aw), len(bw))


def _request_with_backoff(method, url, **kwargs):
    """GET/HEAD with exponential backoff on 429 / 5xx."""
    for delay in (0, *RETRY_BACKOFF):
        if delay:
            time.sleep(delay)
        try:
            r = requests.request(method, url, timeout=DEFAULT_TIMEOUT, **kwargs)
        except requests.RequestException:
            continue
        if r.status_code < 500 and r.status_code != 429:
            return r
    return None


# ---- Layer 1 ----------------------------------------------------------------


def layer1_resolve(candidate: dict) -> Optional[tuple[str, str]]:
    """Returns (kind, id) on success; None on failure."""
    if candidate.get("doi"):
        r = _request_with_backoff("HEAD", f"{DOI_BASE}/{candidate['doi']}", allow_redirects=True)
        if r is not None and r.status_code == 200:
            return ("doi", candidate["doi"])

    if candidate.get("arxiv_id"):
        r = _request_with_backoff("GET", f"{ARXIV_BASE}/{candidate['arxiv_id']}")
        if r is not None and r.status_code == 200:
            page_title = ""
            m = re.search(r"<meta name=\"citation_title\" content=\"([^\"]+)\"", r.text)
            if m:
                page_title = m.group(1)
            if title_overlap(candidate.get("title", ""), page_title) >= 0.5:
                return ("arxiv", candidate["arxiv_id"])

    if candidate.get("s2_paper_id"):
        r = _request_with_backoff(
            "GET",
            f"{S2_BASE}/paper/{candidate['s2_paper_id']}",
            headers=_s2_headers(),
        )
        if r is not None and r.status_code == 200:
            return ("s2", candidate["s2_paper_id"])

    return None


# ---- Layer 2 (CrossRef) -----------------------------------------------------


def layer2_crossref_match(candidate: dict) -> bool:
    if not candidate.get("doi"):
        return True  # nothing to check; not a fail
    r = _request_with_backoff("GET", f"{CROSSREF_BASE}/{candidate['doi']}")
    if r is None or r.status_code != 200:
        return False
    try:
        m = r.json().get("message", {})
    except ValueError:
        return False

    crossref_title = (m.get("title") or [""])[0]
    if title_overlap(candidate.get("title", ""), crossref_title) < 0.7:
        return False

    if candidate.get("first_author_lastname"):
        authors = m.get("author") or []
        if not authors:
            return False
        first_family = authors[0].get("family", "")
        if first_family.lower() != candidate["first_author_lastname"].lower():
            return False

    if candidate.get("year"):
        date_parts = m.get("published", {}).get("date-parts") or m.get("issued", {}).get("date-parts") or [[None]]
        cr_year = date_parts[0][0] if date_parts and date_parts[0] else None
        if cr_year and abs(int(cr_year) - int(candidate["year"])) > 1:
            return False

    return True


# ---- Layer 3 (S2 triangulation) --------------------------------------------


def layer3_s2_triangulate(candidate: dict) -> bool:
    title = candidate.get("title", "")
    if not title:
        return False
    r = _request_with_backoff(
        "GET",
        f"{S2_BASE}/paper/search",
        params={"query": title, "limit": 5, "fields": "title,authors,year"},
        headers=_s2_headers(),
    )
    if r is None or r.status_code != 200:
        return False
    try:
        hits = r.json().get("data") or []
    except ValueError:
        return False
    if not hits:
        return False
    top = hits[0]
    if title_overlap(title, top.get("title", "")) < 0.8:
        return False
    if candidate.get("first_author_lastname"):
        first_authors = top.get("authors") or []
        if not first_authors:
            return False
        family = first_authors[0].get("name", "").split()[-1]
        if family.lower() != candidate["first_author_lastname"].lower():
            return False
    if candidate.get("year") and top.get("year"):
        if abs(int(top["year"]) - int(candidate["year"])) > 1:
            return False
    return True


# ---- Pipeline ---------------------------------------------------------------


def verify_one(candidate: dict) -> dict:
    via = []
    l1 = layer1_resolve(candidate)
    if not l1:
        return {**candidate, "verification_failed": "layer1_no_resolver"}
    via.append(f"{l1[0]}:200ok")

    if candidate.get("doi") and not layer2_crossref_match(candidate):
        return {**candidate, "verification_failed": "layer2_metadata_mismatch"}
    if candidate.get("doi"):
        via.append("crossref:match")

    if not layer3_s2_triangulate(candidate):
        return {**candidate, "verification_failed": "layer3_no_s2_match"}
    via.append("s2_triangulate:match")

    return {**candidate, "verified_via": via}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()

    with open(args.input) as f:
        candidates = json.load(f)
    if not isinstance(candidates, list):
        sys.exit("Input must be a JSON list of candidates.")

    verified = [None] * len(candidates)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        future_to_idx = {ex.submit(verify_one, c): i for i, c in enumerate(candidates)}
        for fut in as_completed(future_to_idx):
            verified[future_to_idx[fut]] = fut.result()

    with open(args.output, "w") as f:
        json.dump(verified, f, indent=2)

    n_pass = sum(1 for v in verified if "verified_via" in v)
    n_fail = sum(1 for v in verified if "verification_failed" in v)
    print(f"Verified {n_pass}/{len(verified)} ({n_fail} failed).", file=sys.stderr)


if __name__ == "__main__":
    main()
