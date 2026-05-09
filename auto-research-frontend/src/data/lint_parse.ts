import type { LintFinding, LintHeader, LintReport } from "./types";

const HEADER_RE = /<!--\s*auto-research lint_report v1\s*([\s\S]+?)-->/;
const SECTION_RE = /^## (?<rule>[\w-]+)\s*$/;
const FINDING_RE = /^- \*\*(?<locator>[^*]+)\*\* — (?<message>.+)$/;
const EXTRA_RE = /^\s*-\s*(?<key>[\w-]+):\s*(?<value>.+)$/;
const CONTEXT_RE = /^\s*-\s*context:\s*`(?<ctx>[\s\S]*?)`\s*$/;

function parseHeader(raw: string): LintHeader {
  const m = HEADER_RE.exec(raw);
  if (!m) return {};
  const blob = m[1].trim();
  const start = blob.indexOf("{");
  if (start < 0) return {};
  try {
    return JSON.parse(blob.slice(start)) as LintHeader;
  } catch {
    return {};
  }
}

function parseLocator(loc: string): { line: number; col: number } {
  const m = /:L(\d+)(?::C(\d+))?/.exec(loc);
  if (!m) return { line: 0, col: 0 };
  return { line: Number(m[1]), col: m[2] ? Number(m[2]) : 0 };
}

export function parseLintReport(raw: string): LintReport {
  const header = parseHeader(raw);
  const findings: LintFinding[] = [];

  let currentRule = "";
  let current: LintFinding | null = null;
  for (const line of raw.split(/\r?\n/)) {
    const sec = SECTION_RE.exec(line);
    if (sec && sec.groups) {
      currentRule = sec.groups.rule;
      current = null;
      continue;
    }
    const find = FINDING_RE.exec(line);
    if (find && find.groups && currentRule) {
      const { line: ln, col } = parseLocator(find.groups.locator);
      current = {
        rule: currentRule,
        locator: find.groups.locator,
        line: ln,
        col,
        message: find.groups.message.trim(),
        extras: {},
      };
      findings.push(current);
      continue;
    }
    if (current) {
      const ctx = CONTEXT_RE.exec(line);
      if (ctx && ctx.groups) {
        current.context = ctx.groups.ctx;
        continue;
      }
      const extra = EXTRA_RE.exec(line);
      if (extra && extra.groups) {
        current.extras[extra.groups.key] = extra.groups.value.trim();
      }
    }
  }

  const byLine: Record<number, LintFinding[]> = {};
  for (const f of findings) {
    (byLine[f.line] ??= []).push(f);
  }

  return { raw, header, findings, byLine };
}
