import Papa from "papaparse";
import type {
  BibEntry,
  ClaimsLedgerEntry,
  PoolEntry,
  ResultsRow,
  ResultsSummary,
  RunBundle,
  RunYaml,
} from "./types";
import { parseLintReport } from "./lint_parse";

/** Fetch text or null on any error / missing file. */
async function fetchText(path: string): Promise<string | null> {
  try {
    const resp = await fetch(path);
    if (!resp.ok) return null;
    return await resp.text();
  } catch (_err) {
    return null;
  }
}

async function fetchJson<T>(path: string): Promise<T | null> {
  const text = await fetchText(path);
  if (text == null) return null;
  try {
    return JSON.parse(text) as T;
  } catch {
    return null;
  }
}

function parseJsonl<T>(text: string): T[] {
  const out: T[] = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) continue;
    try {
      out.push(JSON.parse(line) as T);
    } catch {
      // skip malformed line, surface as a warning upstream if needed
    }
  }
  return out;
}

/** Tiny YAML reader — only supports the flat keys we care about in run.yaml. */
function parseRunYaml(text: string): RunYaml {
  const out: RunYaml = {};
  let lastKey: string | null = null;
  let nested: Record<string, unknown> | null = null;
  for (const raw of text.split(/\r?\n/)) {
    if (!raw.trim() || raw.trimStart().startsWith("#")) continue;
    const indent = raw.length - raw.trimStart().length;
    const line = raw.trim();
    const match = /^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$/.exec(line);
    if (!match) continue;
    const [, key, valueRaw] = match;
    const value = valueRaw.trim();
    if (indent === 0) {
      lastKey = key;
      nested = null;
      if (value === "") {
        nested = {};
        (out as Record<string, unknown>)[key] = nested;
      } else {
        (out as Record<string, unknown>)[key] = coerce(value);
      }
    } else if (nested && lastKey) {
      nested[key] = coerce(value);
    }
  }
  return out;
}

function coerce(s: string): unknown {
  if (s === "") return "";
  if (s === "true") return true;
  if (s === "false") return false;
  if (/^-?\d+$/.test(s)) return Number(s);
  if (/^-?\d+\.\d+$/.test(s)) return Number(s);
  return s.replace(/^['"]|['"]$/g, "");
}

/** Tiny .bib parser — extracts the cite-key and a few common fields per entry. */
function parseBib(text: string): BibEntry[] {
  const out: BibEntry[] = [];
  const re = /@(\w+)\s*\{\s*([^,\s]+)\s*,([\s\S]*?)\n\}/g;
  for (let m: RegExpExecArray | null; (m = re.exec(text)); ) {
    const [, kind, key, body] = m;
    const fields: Record<string, string> = { entry_type: kind.toLowerCase() };
    const fieldRe = /([A-Za-z_]+)\s*=\s*[{\"]?([^,\n]+?)[}\"]?\s*(?:,|$)/g;
    for (let f: RegExpExecArray | null; (f = fieldRe.exec(body)); ) {
      fields[f[1].toLowerCase()] = f[2].trim().replace(/^[{\"]+|[}\"]+$/g, "");
    }
    out.push({ key, entry_type: fields.entry_type, ...fields });
  }
  return out;
}

export interface FetchOptions {
  base?: string;          // e.g. "./"
  fixture?: string;       // e.g. "dirty" — if set, base becomes "/src/fixtures/<fixture>/"
}

/** Load every artifact the Inspector might display. Anything missing
 *  becomes null/[] without aborting the load — the UI renders banners. */
export async function fetchBundle(opts: FetchOptions = {}): Promise<RunBundle> {
  const base = opts.fixture
    ? `/src/fixtures/${opts.fixture}/`
    : opts.base ?? "./";
  const warnings: string[] = [];

  const [
    runText,
    paperTex,
    bibText,
    ledgerText,
    csvText,
    summary,
    poolData,
    lintText,
  ] = await Promise.all([
    fetchText(`${base}run.yaml`),
    fetchText(`${base}paper.tex`),
    fetchText(`${base}references.bib`),
    fetchText(`${base}claims_ledger.jsonl`),
    fetchText(`${base}results.csv`),
    fetchJson<ResultsSummary>(`${base}results_summary.json`),
    fetchJson<unknown>(`${base}literature_pool.json`),
    fetchText(`${base}lint_report.md`),
  ]);

  if (!paperTex) warnings.push("paper.tex not found — Inspector cannot render claims.");
  if (!ledgerText) warnings.push("claims_ledger.jsonl missing — verification quality reduced.");
  if (!lintText) warnings.push("lint_report.md missing — claims will not be coloured. Run lint_writeup.py first.");
  if (!summary) warnings.push("results_summary.json missing — evidence pane will fall back to results.csv.");

  const rows: ResultsRow[] = csvText
    ? (Papa.parse<ResultsRow>(csvText, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
      }).data as ResultsRow[])
    : [];

  let pool: PoolEntry[] = [];
  if (Array.isArray(poolData)) {
    pool = poolData as PoolEntry[];
  } else if (poolData && typeof poolData === "object") {
    pool = ((poolData as { entries?: PoolEntry[] }).entries ?? []) as PoolEntry[];
  }

  return {
    run: runText ? parseRunYaml(runText) : null,
    paperTex,
    bib: bibText ? parseBib(bibText) : [],
    claims: ledgerText ? parseJsonl<ClaimsLedgerEntry>(ledgerText) : [],
    results: { rows, summary: summary ?? null },
    pool,
    lintReport: lintText ? parseLintReport(lintText) : null,
    fixtureName: opts.fixture,
    warnings,
  };
}
