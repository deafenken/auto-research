// A deliberately small TeX tokenizer for the Inspector. We do NOT try to
// fully render LaTeX — the goal is "wrap every \cite{} and every numeric
// literal in clickable spans, leave the rest as <pre> text". Math chunks
// are extracted so the renderer can hand them to KaTeX.
//
// Locator scheme matches `_lint_common.py::offset_to_line_col`.

export type Token =
  | { kind: "text"; text: string; line: number }
  | { kind: "math"; tex: string; display: boolean; line: number }
  | { kind: "cite"; keys: string[]; raw: string; line: number; col: number }
  | { kind: "number"; value: number; raw: string;
      bold: boolean; pct: boolean; line: number; col: number;
      claimId?: string };

const CITE_RE = /\\cite[a-zA-Z*]*(?:\[[^\]]*\])?\{([^}]+)\}/y;
// Number patterns — must mirror _lint_common.py's order: most-specific first.
const NUM_RE = /\\textbf\{([+-]?\d+(?:\.\d+)?)\\?(%?)\}|([+-]?\d+(?:\.\d+)?[eE][+-]?\d+)|((?<![\d.])[+-]?\d+(?:\.\d+)?\\?%)|((?<![\d.\w])[+-]?\d+\.\d+(?![\d.\w]))/y;
const COMMENT_RE = /(?<!\\)%[^\n]*/g;

function lineColAt(text: string, offset: number): { line: number; col: number } {
  let line = 1;
  let lineStart = 0;
  for (let i = 0; i < offset; i++) {
    if (text.charCodeAt(i) === 10) {
      line++;
      lineStart = i + 1;
    }
  }
  return { line, col: offset - lineStart + 1 };
}

interface Span { start: number; end: number; emit: Token; }

function findCites(text: string): Span[] {
  const spans: Span[] = [];
  CITE_RE.lastIndex = 0;
  for (let i = 0; i < text.length; i++) {
    CITE_RE.lastIndex = i;
    const m = CITE_RE.exec(text);
    if (!m) continue;
    const keys = m[1].split(",").map((s) => s.trim()).filter(Boolean);
    const { line, col } = lineColAt(text, i);
    spans.push({
      start: i,
      end: i + m[0].length,
      emit: { kind: "cite", keys, raw: m[0], line, col },
    });
    i = i + m[0].length - 1;
  }
  return spans;
}

function findNumbers(text: string): Span[] {
  const spans: Span[] = [];
  NUM_RE.lastIndex = 0;
  for (let i = 0; i < text.length; i++) {
    NUM_RE.lastIndex = i;
    const m = NUM_RE.exec(text);
    if (!m) continue;
    const raw = m[0];
    let value: number;
    let bold = false;
    let pct = false;
    if (m[1] != null) {
      bold = true;
      pct = m[2] === "%";
      value = Number(m[1]);
    } else if (m[3] != null) {
      value = Number(m[3]);
    } else if (m[4] != null) {
      pct = true;
      value = Number(m[4].replace(/\\?%$/, ""));
    } else if (m[5] != null) {
      value = Number(m[5]);
    } else {
      i = i + raw.length - 1;
      continue;
    }
    if (Number.isNaN(value)) {
      i = i + raw.length - 1;
      continue;
    }
    const { line, col } = lineColAt(text, i);
    spans.push({
      start: i,
      end: i + raw.length,
      emit: { kind: "number", value, raw, bold, pct, line, col },
    });
    i = i + raw.length - 1;
  }
  return spans;
}

/** $...$ and $$...$$ math blocks. Tracks dollar pairing left-to-right. */
function findMath(text: string): Span[] {
  const spans: Span[] = [];
  let i = 0;
  while (i < text.length) {
    const ch = text[i];
    if (ch === "\\" && text[i + 1]) {
      i += 2;
      continue;
    }
    if (ch === "$") {
      const display = text[i + 1] === "$";
      const open = display ? i + 2 : i + 1;
      const close = display
        ? text.indexOf("$$", open)
        : findSingleDollarClose(text, open);
      if (close < 0) break;
      const tex = text.slice(open, close);
      const { line } = lineColAt(text, i);
      spans.push({
        start: i,
        end: display ? close + 2 : close + 1,
        emit: { kind: "math", tex, display, line },
      });
      i = display ? close + 2 : close + 1;
      continue;
    }
    i++;
  }
  return spans;
}

function findSingleDollarClose(text: string, from: number): number {
  for (let j = from; j < text.length; j++) {
    if (text[j] === "\\") { j++; continue; }
    if (text[j] === "$") return j;
  }
  return -1;
}

function stripComments(text: string): string {
  return text.replace(COMMENT_RE, "");
}

function mergeSorted(spans: Span[][]): Span[] {
  const flat = spans.flat().sort((a, b) => a.start - b.start);
  const out: Span[] = [];
  for (const s of flat) {
    if (out.length && s.start < out[out.length - 1].end) continue; // skip overlapping
    out.push(s);
  }
  return out;
}

export function tokenize(rawTex: string): Token[] {
  const text = stripComments(rawTex);
  // Order matters when spans overlap: cites first (they shouldn't overlap math
  // or numbers in well-formed papers, but we still drop any overlapping span).
  const spans = mergeSorted([findMath(text), findCites(text), findNumbers(text)]);

  const out: Token[] = [];
  let cursor = 0;
  let line = 1;
  for (const span of spans) {
    if (cursor < span.start) {
      const chunk = text.slice(cursor, span.start);
      out.push({ kind: "text", text: chunk, line });
      line += (chunk.match(/\n/g) ?? []).length;
    }
    out.push(span.emit);
    if (span.emit.kind === "math" || span.emit.kind === "text") {
      // line tracking already handled
    } else if (span.emit.kind === "cite" || span.emit.kind === "number") {
      // single-line in practice; keep the line counter monotonic
      line = Math.max(line, span.emit.line);
    }
    cursor = span.end;
  }
  if (cursor < text.length) {
    out.push({ kind: "text", text: text.slice(cursor), line });
  }
  return out;
}

/** Build "paper.tex:L<line>:C<col>" matching the linter / contract convention. */
export function locatorFor(token: Extract<Token, { line: number; col: number }>): string {
  return `paper.tex:L${token.line}:C${token.col}`;
}
