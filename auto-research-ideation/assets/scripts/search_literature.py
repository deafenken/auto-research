#!/usr/bin/env python3
"""
Build the Stage 1 literature pool by querying Semantic Scholar, arXiv,
and OpenReview. Writes a `literature_pool.json` matching the schema in
references/search-protocols.md.

Usage:
    python search_literature.py \
        --domain "test-time compute scaling for small LMs" \
        --keywords "test-time compute,inference scaling,small language model" \
        --years 2 \
        --max-papers 30 \
        --output literature_pool.json

If SEMANTIC_SCHOLAR_API_KEY is set in env, it is used (higher rate limits).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from typing import Iterable, Optional

import requests


S2_BASE = "https://api.semanticscholar.org/graph/v1"
ARXIV_QUERY = "http://export.arxiv.org/api/query"
OPENREVIEW_BASE = "https://api2.openreview.net"

S2_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
DEFAULT_TIMEOUT = 30


def _s2_headers() -> dict:
    return {"x-api-key": S2_API_KEY} if S2_API_KEY else {}


def normalize_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def canonical_key(paper: dict) -> tuple[str, str]:
    if paper.get("doi"):
        return ("doi", paper["doi"].lower())
    if paper.get("arxiv_id"):
        return ("arxiv", paper["arxiv_id"].split("v")[0])
    if paper.get("s2_paper_id"):
        return ("s2", paper["s2_paper_id"])
    return ("title", normalize_title(paper.get("title", "")))


# ---- Semantic Scholar -------------------------------------------------------


def s2_search(query: str, year_range: tuple[int, int], limit: int = 50) -> list[dict]:
    fields = ",".join([
        "paperId", "title", "abstract", "year", "authors", "venue",
        "citationCount", "influentialCitationCount", "openAccessPdf",
        "externalIds", "tldr",
    ])
    params = {
        "query": query,
        "year": f"{year_range[0]}-{year_range[1]}",
        "fieldsOfStudy": "Computer Science",
        "fields": fields,
        "limit": limit,
    }
    for attempt in range(4):
        r = requests.get(f"{S2_BASE}/paper/search", params=params,
                         headers=_s2_headers(), timeout=DEFAULT_TIMEOUT)
        if r.status_code == 200:
            return r.json().get("data") or []
        if r.status_code == 429:
            time.sleep([5, 15, 45, 120][attempt])
            continue
        break
    return []


def s2_to_record(p: dict) -> dict:
    ext = p.get("externalIds") or {}
    return {
        "title": p.get("title", "").strip(),
        "authors": [a.get("name", "") for a in (p.get("authors") or [])],
        "year": p.get("year"),
        "venue": p.get("venue"),
        "abstract": p.get("abstract"),
        "citation_count": p.get("citationCount"),
        "influential_citation_count": p.get("influentialCitationCount"),
        "doi": ext.get("DOI"),
        "arxiv_id": ext.get("ArXiv"),
        "s2_paper_id": p.get("paperId"),
        "url": (p.get("openAccessPdf") or {}).get("url")
                or (f"https://arxiv.org/abs/{ext['ArXiv']}" if ext.get("ArXiv") else None),
        "verified_via": ["s2:search"],
    }


# ---- arXiv ------------------------------------------------------------------


ARXIV_NS = {"a": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom"}


def arxiv_search(query: str, max_results: int = 50, category: str = "cs.LG") -> list[dict]:
    search_query = f"cat:{category} AND (ti:\"{query}\" OR abs:\"{query}\")"
    params = {
        "search_query": search_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }
    r = requests.get(ARXIV_QUERY, params=params, timeout=DEFAULT_TIMEOUT)
    if r.status_code != 200:
        return []
    root = ET.fromstring(r.text)
    out = []
    for entry in root.findall("a:entry", ARXIV_NS):
        title = (entry.findtext("a:title", default="", namespaces=ARXIV_NS) or "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=ARXIV_NS) or "").strip()
        published = entry.findtext("a:published", default="", namespaces=ARXIV_NS) or ""
        year = int(published[:4]) if published[:4].isdigit() else None
        arxiv_id = ""
        id_url = entry.findtext("a:id", default="", namespaces=ARXIV_NS) or ""
        m = re.search(r"abs/([\w.\-]+)", id_url)
        if m:
            arxiv_id = m.group(1)
        authors = [a.findtext("a:name", default="", namespaces=ARXIV_NS) or ""
                   for a in entry.findall("a:author", ARXIV_NS)]
        out.append({
            "title": title,
            "authors": authors,
            "year": year,
            "venue": "arXiv preprint",
            "abstract": summary,
            "citation_count": None,
            "influential_citation_count": None,
            "doi": None,
            "arxiv_id": arxiv_id,
            "s2_paper_id": None,
            "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
            "verified_via": ["arxiv:search"],
        })
    time.sleep(3.0)  # be polite
    return out


# ---- OpenReview (gap mining only) ------------------------------------------


NEGATIVE_MARKERS = [
    "limitation", "however", "weakness", "would be stronger if", "fails to",
    "does not address", "doesn't generalize", "unclear how", "concerned that",
    "missing comparison", "would benefit from",
]


def openreview_iclr_gaps(keyword: str, year: int, max_papers: int = 10) -> list[dict]:
    """Returns extracted negative quotes from ICLR review threads."""
    venue = f"ICLR.cc/{year}/Conference"
    try:
        r = requests.get(f"{OPENREVIEW_BASE}/notes/search",
                         params={"group": venue, "content.title": keyword, "limit": max_papers},
                         timeout=DEFAULT_TIMEOUT)
    except requests.RequestException:
        return []
    if r.status_code != 200:
        return []
    notes = (r.json() or {}).get("notes") or []
    out = []
    for n in notes[:max_papers]:
        forum_id = n.get("id") or n.get("forum")
        if not forum_id:
            continue
        try:
            rr = requests.get(f"{OPENREVIEW_BASE}/notes",
                              params={"forum": forum_id, "details": "replies"},
                              timeout=DEFAULT_TIMEOUT)
        except requests.RequestException:
            continue
        if rr.status_code != 200:
            continue
        replies = (rr.json() or {}).get("notes") or []
        quotes = []
        for rep in replies:
            sigs = rep.get("signatures") or []
            if not any("Reviewer" in s for s in sigs):
                continue
            content = rep.get("content") or {}
            for field in ("strengths_and_weaknesses", "questions", "limitations"):
                text = content.get(field)
                if isinstance(text, dict):
                    text = text.get("value", "")
                if not text:
                    continue
                for sentence in re.split(r"(?<=[.!?])\s+", text):
                    if any(marker in sentence.lower() for marker in NEGATIVE_MARKERS):
                        quotes.append(sentence.strip())
        if quotes:
            out.append({
                "paper_id": forum_id,
                "title": (n.get("content") or {}).get("title", {}).get("value", ""),
                "negative_quotes": quotes[:10],
            })
        time.sleep(0.5)
    return out


# ---- Pipeline ---------------------------------------------------------------


def dedupe(papers: Iterable[dict]) -> list[dict]:
    seen: dict[tuple[str, str], dict] = {}
    for p in papers:
        key = canonical_key(p)
        existing = seen.get(key)
        if not existing or sum(1 for v in p.values() if v) > sum(1 for v in existing.values() if v):
            seen[key] = p
    return list(seen.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, help="One-line description of the domain")
    ap.add_argument("--keywords", required=True, help="Comma-separated keyword list to search")
    ap.add_argument("--years", type=int, default=2, help="How many years back from today")
    ap.add_argument("--max-papers", type=int, default=30)
    ap.add_argument("--arxiv-category", default="cs.LG")
    ap.add_argument("--openreview-year", type=int, default=None,
                    help="ICLR year to mine for reviewer comments (default: previous year)")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    today = dt.date.today()
    year_range = (today.year - args.years, today.year)
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    or_year = args.openreview_year or (today.year - 1)

    queries_run: list[str] = []
    raw: list[dict] = []

    for kw in keywords:
        queries_run.append(f"s2:{kw}")
        raw.extend(s2_to_record(p) for p in s2_search(kw, year_range, limit=30))
        queries_run.append(f"arxiv:{kw}")
        raw.extend(arxiv_search(kw, max_results=20, category=args.arxiv_category))

    pool = dedupe(raw)
    pool.sort(
        key=lambda p: (
            (p.get("influential_citation_count") or 0),
            (p.get("citation_count") or 0),
            (p.get("year") or 0),
        ),
        reverse=True,
    )
    pool = pool[: args.max_papers]

    openreview_extracts = []
    for kw in keywords[:2]:
        queries_run.append(f"openreview:{kw}@ICLR{or_year}")
        openreview_extracts.extend(openreview_iclr_gaps(kw, or_year, max_papers=5))

    output = {
        "fetched_at": dt.datetime.utcnow().isoformat() + "Z",
        "domain": args.domain,
        "queries_run": queries_run,
        "papers": pool,
        "openreview_extracts": openreview_extracts,
    }
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote {len(pool)} papers + {len(openreview_extracts)} OpenReview extracts to {args.output}")


if __name__ == "__main__":
    main()
