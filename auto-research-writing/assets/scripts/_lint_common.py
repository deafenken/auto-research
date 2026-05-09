#!/usr/bin/env python3
"""Shared helpers for Stage-4 integrity linters.

Two linters consume this:
* ``check_citations.py`` (Layer-4 citation relevance)
* ``trace_numbers.py`` (numeric-claim provenance)

Both linters parse ``paper.tex`` with a small line-tracking regex scanner —
deliberately lighter than ``pylatexenc`` so the scripts run on minimal
environments without a torch / anthropic install. A higher-fidelity parser
can be swapped in here without touching either CLI.
"""
from __future__ import annotations

import dataclasses
import datetime as _dt
import json
import os
import pathlib
import re
import sys
import tempfile
from typing import Iterable

# Strip TeX line comments before scanning (preserve escaped %).
_COMMENT_RE = re.compile(r"(?<!\\)%[^\n]*")
# A \cite{...} (\citep, \citet, \citeyear, etc.) — capture inner key list.
_CITE_RE = re.compile(r"\\cite[a-zA-Z*]*(?:\[[^\]]*\])?\{(?P<keys>[^}]+)\}")
# Numeric literals worth tracing. Order matters: most-specific first.
_NUMBER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("bold_pct", re.compile(r"\\textbf\{(?P<value>[+-]?\d+(?:\.\d+)?)\\?%\}")),
    ("bold",    re.compile(r"\\textbf\{(?P<value>[+-]?\d+(?:\.\d+)?)\}")),
    ("sci",     re.compile(r"(?<![\w\d])(?P<value>[+-]?\d+(?:\.\d+)?[eE][+-]?\d+)(?![\w\d])")),
    ("pct",     re.compile(r"(?<![\d.])(?P<value>[+-]?\d+(?:\.\d+)?)\\?%(?![A-Za-z])")),
    ("plain",   re.compile(r"(?<![\d.\w])(?P<value>[+-]?\d+\.\d+)(?![\d\w])")),
)
# Allowlists — these literals are informational, never untraced violations.
_ALLOW_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("section",   re.compile(r"\b[Ss]ec(?:tion)?s?[.~ ]\s*\d+(?:\.\d+)*\b")),
    ("figure",    re.compile(r"\b[Ff]ig(?:ure)?s?[.~ ]\s*\d+\b")),
    ("table",     re.compile(r"\b[Tt]ab(?:le)?s?[.~ ]\s*\d+\b")),
    ("equation",  re.compile(r"\b[Ee]q(?:uation)?s?[.~ ]\s*\(?\d+\)?\b")),
    ("citeyear",  re.compile(r"\b[A-Z][a-z]+(?:\s+et al\.?)?,?\s*\d{4}\b")),
    ("page",      re.compile(r"\bp\.\s*\d+\b")),
    ("ref_macro", re.compile(r"\\(?:label|ref|eqref|cref|Cref|autoref)\{[^}]+\}")),
    ("year_paren",re.compile(r"\((?:19|20)\d{2}[a-z]?\)")),
)


@dataclasses.dataclass
class TexCitation:
    keys: list[str]
    line: int
    col: int
    raw: str
    context: str

    @property
    def locator(self) -> str:
        return f"paper.tex:L{self.line}:C{self.col}"


@dataclasses.dataclass
class TexNumber:
    value: float
    raw: str
    line: int
    col: int
    kind: str          # "bold_pct" / "bold" / "sci" / "pct" / "plain"
    context: str
    nearest_cite_keys: list[str]

    @property
    def locator(self) -> str:
        return f"paper.tex:L{self.line}:C{self.col}"


@dataclasses.dataclass
class Finding:
    rule: str          # e.g. "citation-relevance", "number-untraced"
    severity: str      # "error" | "warning" | "info"
    locator: str
    snippet: str
    message: str
    extras: dict

    def to_markdown(self) -> str:
        head = f"- **{self.locator}** — {self.message}"
        sub = []
        if self.snippet:
            sub.append(f"  - context: `{self.snippet}`")
        for k, v in sorted(self.extras.items()):
            sub.append(f"  - {k}: {v}")
        return "\n".join([head, *sub])


def strip_comments(text: str) -> str:
    return _COMMENT_RE.sub("", text)


def offset_to_line_col(text: str, offset: int) -> tuple[int, int]:
    """Return 1-based line and column for a byte offset in ``text``."""
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset) + 1
    col = offset - line_start + 1
    return line, col


def context_window(text: str, start: int, end: int, width: int = 60) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    snippet = text[left:right].replace("\n", " ")
    return snippet.strip()


def find_citations(tex: str, context_words: int = 40) -> list[TexCitation]:
    out: list[TexCitation] = []
    for match in _CITE_RE.finditer(tex):
        keys = [k.strip() for k in match["keys"].split(",") if k.strip()]
        line, col = offset_to_line_col(tex, match.start())
        words_left = " ".join(tex[:match.start()].split()[-context_words:])
        words_right = " ".join(tex[match.end():].split()[:context_words])
        ctx = (words_left + " [CITE] " + words_right).strip()
        out.append(TexCitation(keys=keys, line=line, col=col,
                                raw=match.group(0), context=ctx))
    return out


def _is_allowlisted(window: str) -> str | None:
    for kind, pat in _ALLOW_PATTERNS:
        if pat.search(window):
            return kind
    return None


def find_numbers(tex: str, cite_proximity_chars: int = 30) -> list[TexNumber]:
    found: list[TexNumber] = []
    seen_spans: list[tuple[int, int]] = []
    for kind, pattern in _NUMBER_PATTERNS:
        for match in pattern.finditer(tex):
            span = match.span()
            # Skip overlap with already-claimed (more specific) match.
            if any(not (span[1] <= s or span[0] >= e) for s, e in seen_spans):
                continue
            seen_spans.append(span)

            window_left = max(0, span[0] - 24)
            window_right = min(len(tex), span[1] + 24)
            check_window = tex[window_left:window_right]
            if _is_allowlisted(check_window):
                continue

            try:
                value = float(match["value"])
            except ValueError:
                continue
            line, col = offset_to_line_col(tex, span[0])
            ctx = context_window(tex, span[0], span[1])

            cite_window = tex[max(0, span[0] - cite_proximity_chars): span[0]]
            cite_keys: list[str] = []
            cite_match = list(_CITE_RE.finditer(cite_window))
            if cite_match:
                cite_keys = [k.strip() for k in cite_match[-1]["keys"].split(",") if k.strip()]

            found.append(TexNumber(value=value, raw=match.group(0),
                                    line=line, col=col, kind=kind,
                                    context=ctx, nearest_cite_keys=cite_keys))
    found.sort(key=lambda n: (n.line, n.col))
    return found


@dataclasses.dataclass
class LintReport:
    paper_path: pathlib.Path
    out_path: pathlib.Path
    findings: list[Finding] = dataclasses.field(default_factory=list)
    counts: dict[str, dict[str, int]] = dataclasses.field(default_factory=dict)
    linters_run: list[str] = dataclasses.field(default_factory=list)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def add_count(self, section: str, label: str, n: int = 1) -> None:
        self.counts.setdefault(section, {})
        self.counts[section][label] = self.counts[section].get(label, 0) + n

    @property
    def exit_code(self) -> int:
        return 1 if any(f.severity == "error" for f in self.findings) else 0

    def write(self) -> None:
        sections: dict[str, list[Finding]] = {}
        for f in self.findings:
            sections.setdefault(f.rule, []).append(f)

        timestamp = (
            os.environ.get("LINT_FREEZE_TIME")
            or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        header = {
            "schema": "auto-research lint_report v1",
            "generated_at": timestamp,
            "paper": str(self.paper_path),
            "linters_run": sorted(self.linters_run),
            "exit_code": self.exit_code,
            "counts": self.counts,
        }
        lines = [
            f"<!-- auto-research lint_report v1 {json.dumps(header, sort_keys=True)} -->",
            "",
            f"# Lint Report — {self.paper_path}",
            "",
        ]
        if not self.findings:
            lines.append("No violations.")
        for section in sorted(sections):
            lines.append(f"## {section}")
            for finding in sorted(sections[section], key=lambda f: f.locator):
                lines.append(finding.to_markdown())
            lines.append("")

        body = "\n".join(lines).rstrip() + "\n"
        # Atomic write: temp file + rename.
        with tempfile.NamedTemporaryFile("w", delete=False,
                                          dir=str(self.out_path.parent),
                                          encoding="utf-8") as tmp:
            tmp.write(body)
            tmp_path = pathlib.Path(tmp.name)
        os.replace(tmp_path, self.out_path)


def load_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.is_file():
        return []
    out: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f"[lint] skipping bad jsonl line in {path}: {exc}", file=sys.stderr)
    return out


def parse_bib_keys(bib_path: pathlib.Path) -> dict[str, dict]:
    """Tiny bib parser — extracts ``key`` and selected fields per entry.

    We only need the cite-key index, so this avoids the bibtexparser dep.
    """
    if not bib_path.is_file():
        return {}
    text = bib_path.read_text()
    out: dict[str, dict] = {}
    for entry in re.finditer(r"@(?P<kind>\w+)\s*\{\s*(?P<key>[^,\s]+)\s*,(?P<body>.*?)\n\}",
                              text, flags=re.DOTALL):
        body = entry["body"]
        fields = dict(out_field_iter(body))
        fields["entry_type"] = entry["kind"].lower()
        out[entry["key"]] = fields
    return out


def out_field_iter(body: str) -> Iterable[tuple[str, str]]:
    for fmatch in re.finditer(r"(?P<name>[A-Za-z]+)\s*=\s*[{\"]?(?P<value>[^,\n]+?)[}\"]?\s*(?:,|$)",
                               body):
        yield fmatch["name"].lower(), fmatch["value"].strip().strip("{}").strip()
