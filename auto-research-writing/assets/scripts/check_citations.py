#!/usr/bin/env python3
"""Stage-4 citation-relevance linter (Layer 4).

For every ``\\cite{key}`` in ``paper.tex``:

1. Resolve ``key`` against ``references.bib``.
2. Map the bib entry to a verified record in
   ``stage1_ideation/literature_pool.json`` (Layer 1–3 already validated
   identifier + metadata; Layer 4 covers *whether the cited paper actually
   supports the local claim*).
3. Decide SUPPORTS / MENTIONS / IRRELEVANT via a pluggable judge:
   * ``none``    — skip the relevance call; only check BIB-missing-from-pool.
   * ``mock``    — read deterministic labels from ``--judge-mock-file`` (tests).
   * ``scicite`` — lazy-loaded ``allenai/scicite`` model (offline, fast).
   * ``llm``     — single-shot Claude call per cite (slower, captures semantics).
   * ``hybrid``  — SciCite first; escalate to LLM when SciCite confidence is
                   weak or the ablation-attack guard fires.

Bias mitigations baked into ``hybrid`` and ``llm``:
* Default-to-IRRELEVANT framing in the LLM system prompt — counters the
  majority-class bias documented for SciCite (>92% MENTIONS).
* Ablation-attack guard: re-classify with the cite context stripped; if the
  label and confidence stay nearly identical, the citation isn't actually
  using the surrounding text → mark IRRELEVANT-BY-ABLATION.
* LLM may only override a SciCite SUPPORTS/MENTIONS verdict if its own
  confidence ≥ scicite_confidence + 0.15 (corrects lenient self-judging).
* Local response cache keyed by ``sha256(context|title|abstract)`` so
  reruns are cheap and deterministic.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import pathlib
import sys
from typing import Protocol

from _lint_common import (
    Finding,
    LintReport,
    TexCitation,
    find_citations,
    parse_bib_keys,
    strip_comments,
)


# ---- Judge protocol --------------------------------------------------------


@dataclasses.dataclass
class JudgeOut:
    label: str        # "SUPPORTS" | "MENTIONS" | "IRRELEVANT" | "IRRELEVANT-BY-ABLATION"
    confidence: float
    reason: str
    judge_name: str


class Judge(Protocol):
    def label(self, ctx: str, title: str, abstract: str) -> JudgeOut: ...


# ---- None / Mock judges ----------------------------------------------------


class NoneJudge:
    def label(self, ctx: str, title: str, abstract: str) -> JudgeOut:
        return JudgeOut(label="MENTIONS", confidence=0.5,
                        reason="judge=none (bib-only pass)",
                        judge_name="none")


class MockJudge:
    """Deterministic judge driven by a JSON map.

    Map shape::

        {"cite_key": {"label": "SUPPORTS", "confidence": 0.9, "reason": "..."},
         "default":  {"label": "MENTIONS", "confidence": 0.5}}
    """

    def __init__(self, mock_path: pathlib.Path):
        if not mock_path.is_file():
            sys.exit(f"[check_citations] --judge-mock-file {mock_path} not found")
        self._table = json.loads(mock_path.read_text())
        self._current_key: str | None = None

    def set_key(self, key: str) -> None:
        self._current_key = key

    def label(self, ctx: str, title: str, abstract: str) -> JudgeOut:
        entry = self._table.get(self._current_key) or self._table.get("default") or {}
        return JudgeOut(
            label=entry.get("label", "MENTIONS"),
            confidence=float(entry.get("confidence", 0.5)),
            reason=entry.get("reason", "mock"),
            judge_name="mock",
        )


# ---- SciCite judge (lazy import) ------------------------------------------


class ScicJudge:
    _model = None
    _tokenizer = None

    def _ensure(self) -> None:
        if ScicJudge._model is not None:
            return
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:  # pragma: no cover
            sys.exit("[check_citations] --judge scicite needs `transformers` and `torch`. "
                     f"Install them or use `--judge llm|mock|none`. ({exc})")
        ScicJudge._tokenizer = AutoTokenizer.from_pretrained("allenai/scicite")
        ScicJudge._model = AutoModelForSequenceClassification.from_pretrained("allenai/scicite")

    def label(self, ctx: str, title: str, abstract: str) -> JudgeOut:
        self._ensure()
        import torch  # type: ignore[import]
        text = f"{title}. {abstract}\n\nContext: {ctx}"
        enc = ScicJudge._tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = ScicJudge._model(**enc).logits.softmax(dim=-1)[0].tolist()
        # SciCite labels: 0=background, 1=method, 2=result.
        idx = max(range(3), key=lambda i: logits[i])
        confidence = float(logits[idx])
        scicite_label = ["background", "method", "result"][idx]
        # Map to our 3-way: result/method → SUPPORTS, background → MENTIONS.
        ours = "SUPPORTS" if scicite_label in ("method", "result") else "MENTIONS"
        return JudgeOut(label=ours, confidence=confidence,
                        reason=f"scicite={scicite_label}",
                        judge_name="scicite")


# ---- LLM judge (lazy import) ----------------------------------------------


_LLM_PROMPT = """\
You are auditing whether a citation is RELEVANT to its local claim.
Default to IRRELEVANT when the surrounding context does not actually
invoke any specific finding from the cited paper's abstract.

Return ONLY a single JSON object on one line, no prose:
{"label": "SUPPORTS"|"MENTIONS"|"IRRELEVANT",
 "confidence": 0.0-1.0,
 "reason": "<short>",
 "context_changes_label": true|false}

context_changes_label means: "would removing the citation context change my label?"
If false, lower confidence by 0.3 in your reasoning.

CITED PAPER:
Title: {title}
Abstract: {abstract}

LOCAL CONTEXT (surrounding the \\cite{{}} call):
{ctx}
"""


class LLMJudge:
    def __init__(self, model: str = "claude-opus-4-7"):
        self._model = model
        self._client = None

    def _ensure(self) -> None:
        if self._client is not None:
            return
        try:
            import anthropic  # type: ignore[import]
        except ImportError as exc:  # pragma: no cover
            sys.exit("[check_citations] --judge llm needs `anthropic`. "
                     f"Install it or use `--judge mock|none`. ({exc})")
        self._client = anthropic.Anthropic()

    def label(self, ctx: str, title: str, abstract: str) -> JudgeOut:
        self._ensure()
        prompt = _LLM_PROMPT.format(title=title, abstract=abstract[:1200], ctx=ctx[:1200])
        msg = self._client.messages.create(  # type: ignore[union-attr]
            model=self._model,
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
        try:
            parsed = json.loads(text.strip().splitlines()[0])
        except (json.JSONDecodeError, IndexError):
            return JudgeOut(label="IRRELEVANT", confidence=0.0,
                            reason=f"LLM returned non-JSON: {text[:80]!r}",
                            judge_name="llm")
        confidence = float(parsed.get("confidence", 0.5))
        if not parsed.get("context_changes_label", True):
            confidence = max(0.0, confidence - 0.3)
        return JudgeOut(
            label=str(parsed.get("label", "IRRELEVANT")).upper(),
            confidence=confidence,
            reason=str(parsed.get("reason", ""))[:120],
            judge_name="llm",
        )


# ---- Hybrid orchestration -------------------------------------------------


class HybridJudge:
    def __init__(self):
        self._sci = ScicJudge()
        self._llm = LLMJudge()

    def label(self, ctx: str, title: str, abstract: str) -> JudgeOut:
        sci = self._sci.label(ctx, title, abstract)
        # Ablation-attack guard: re-classify with stripped context.
        sci_no_ctx = self._sci.label("[CITE]", title, abstract)
        if sci.label == sci_no_ctx.label and abs(sci.confidence - sci_no_ctx.confidence) < 0.05:
            sci = JudgeOut(label="IRRELEVANT-BY-ABLATION",
                           confidence=sci.confidence,
                           reason="scicite label invariant under context removal",
                           judge_name="scicite+ablation")
        # Escalate to LLM when SciCite is weak or label is MENTIONS.
        if sci.label == "MENTIONS" or sci.confidence < 0.6 or sci.label.startswith("IRRELEVANT"):
            llm = self._llm.label(ctx, title, abstract)
            # LLM may only override SUPPORTS/MENTIONS if it's notably more confident.
            if (llm.label != sci.label
                and llm.confidence < sci.confidence + 0.15
                and not sci.label.startswith("IRRELEVANT")):
                return sci
            return JudgeOut(
                label=llm.label,
                confidence=llm.confidence,
                reason=f"scicite={sci.label}@{sci.confidence:.2f} -> llm={llm.label}: {llm.reason}",
                judge_name="hybrid",
            )
        return sci


# ---- Cache ---------------------------------------------------------------


def _cache_key(ctx: str, title: str, abstract: str, judge_name: str) -> str:
    h = hashlib.sha256()
    h.update(judge_name.encode())
    for chunk in (ctx, title, abstract):
        h.update(b"\x00")
        h.update(chunk.encode())
    return h.hexdigest()


class CachedJudge:
    def __init__(self, inner: Judge, cache_dir: pathlib.Path):
        self._inner = inner
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def label(self, ctx: str, title: str, abstract: str) -> JudgeOut:
        key = _cache_key(ctx, title, abstract, type(self._inner).__name__)
        path = self._dir / f"{key}.json"
        if path.is_file():
            data = json.loads(path.read_text())
            return JudgeOut(**data)
        out = self._inner.label(ctx, title, abstract)
        path.write_text(json.dumps(dataclasses.asdict(out)))
        return out


# ---- Entry point ----------------------------------------------------------


def _build_judge(name: str, mock_path: pathlib.Path | None,
                 cache_dir: pathlib.Path | None) -> Judge:
    inner: Judge
    if name == "none":
        inner = NoneJudge()
    elif name == "mock":
        if mock_path is None:
            sys.exit("[check_citations] --judge mock requires --judge-mock-file")
        inner = MockJudge(mock_path)
    elif name == "scicite":
        inner = ScicJudge()
    elif name == "llm":
        inner = LLMJudge()
    elif name == "hybrid":
        inner = HybridJudge()
    else:
        sys.exit(f"[check_citations] unknown --judge {name!r}")
    if cache_dir is not None and name not in ("none", "mock"):
        return CachedJudge(inner, cache_dir)
    return inner


def _index_pool(pool_data) -> dict:
    if isinstance(pool_data, dict):
        pool = pool_data.get("entries", [])
    else:
        pool = pool_data or []
    out: dict[str, dict] = {}
    for entry in pool:
        for key in (entry.get("cite_key"), entry.get("bibtex_key"),
                    entry.get("s2_paper_id"), entry.get("arxiv_id"), entry.get("doi")):
            if key:
                out[str(key)] = entry
    return out


def _judge_for_cite(judge: Judge, key: str, ctx: str, entry: dict) -> JudgeOut:
    if isinstance(judge, MockJudge):
        judge.set_key(key)
    elif isinstance(judge, CachedJudge) and isinstance(judge._inner, MockJudge):
        judge._inner.set_key(key)
    return judge.label(ctx,
                        entry.get("title") or "",
                        entry.get("abstract") or "")


def _evaluate(citation: TexCitation, judge: Judge, bib: dict, pool: dict,
              report: LintReport) -> None:
    for key in citation.keys:
        bib_entry = bib.get(key)
        if not bib_entry:
            report.add_count("citations", "BIB-MISSING")
            report.add(Finding(
                rule="citation-bib-missing",
                severity="error",
                locator=citation.locator,
                snippet=citation.context,
                message=f"\\cite{{{key}}} resolves to no entry in references.bib",
                extras={"key": key},
            ))
            continue

        pool_entry = (pool.get(key)
                      or pool.get(bib_entry.get("doi", ""))
                      or pool.get(bib_entry.get("arxiv_id", ""))
                      or pool.get(bib_entry.get("s2_paper_id", "")))
        if not pool_entry:
            report.add_count("citations", "POOL-MISSING")
            report.add(Finding(
                rule="citation-pool-missing",
                severity="error",
                locator=citation.locator,
                snippet=citation.context,
                message=f"\\cite{{{key}}} not in literature_pool.json (Layer 1–3 unverified)",
                extras={"key": key, "bib_title": bib_entry.get("title", "")[:80]},
            ))
            continue

        verdict = _judge_for_cite(judge, key, citation.context, pool_entry)
        if verdict.label == "SUPPORTS":
            report.add_count("citations", "SUPPORTS")
            continue
        if verdict.label == "MENTIONS" and verdict.confidence >= 0.5:
            report.add_count("citations", "MENTIONS")
            continue

        severity = "error"
        report.add_count("citations", verdict.label)
        report.add(Finding(
            rule="citation-relevance",
            severity=severity,
            locator=citation.locator,
            snippet=citation.context,
            message=f"\\cite{{{key}}} judged {verdict.label} (conf={verdict.confidence:.2f})",
            extras={
                "key": key,
                "judge": verdict.judge_name,
                "reason": verdict.reason,
                "paper_title": (pool_entry.get("title") or "")[:80],
            },
        ))


def run(report: LintReport, paper: pathlib.Path, run_dir: pathlib.Path,
        bib_path: pathlib.Path | None = None,
        judge_name: str = "hybrid",
        judge_mock_file: pathlib.Path | None = None,
        cache_dir: pathlib.Path | None = pathlib.Path(".cache/citation_judge"),
        warn_only: bool = False) -> None:
    """Populate ``report`` with citation-relevance findings. Caller writes."""
    if not paper.is_file():
        sys.exit(f"[check_citations] {paper} not found")
    bib_path = bib_path or paper.parent / "references.bib"
    pool_path = run_dir / "stage1_ideation" / "literature_pool.json"

    raw_tex = paper.read_text()
    tex = strip_comments(raw_tex)
    citations = find_citations(tex)
    bib = parse_bib_keys(bib_path)
    pool = _index_pool(json.loads(pool_path.read_text())) if pool_path.is_file() else {}

    judge = _build_judge(judge_name, judge_mock_file, cache_dir)
    report.linters_run.append(f"check_citations.py (judge={judge_name})")

    pre_findings = len(report.findings)
    for citation in citations:
        _evaluate(citation, judge, bib, pool, report)

    if warn_only:
        for f in report.findings[pre_findings:]:
            if f.severity == "error":
                f.severity = "warning"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", type=pathlib.Path, required=True)
    parser.add_argument("--bib", type=pathlib.Path, default=None,
                        help="references.bib (default: alongside paper.tex)")
    parser.add_argument("--run-dir", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, default=None)
    parser.add_argument("--judge", choices=["none", "mock", "scicite", "llm", "hybrid"],
                        default=os.environ.get("AUTO_RESEARCH_CITE_JUDGE", "hybrid"))
    parser.add_argument("--judge-mock-file", type=pathlib.Path, default=None)
    parser.add_argument("--cache-dir", type=pathlib.Path,
                        default=pathlib.Path(".cache/citation_judge"))
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    out_path = args.out or args.paper.parent / "lint_report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = LintReport(paper_path=args.paper, out_path=out_path)
    run(report, args.paper, args.run_dir,
        bib_path=args.bib, judge_name=args.judge,
        judge_mock_file=args.judge_mock_file,
        cache_dir=None if args.no_cache else args.cache_dir,
        warn_only=args.warn_only)
    report.write()
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
