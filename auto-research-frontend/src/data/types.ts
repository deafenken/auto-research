// Shared types for the Inspector. Mirrors the contract documented in
// auto-research/references/state-contract.md (v2). Keep field names in sync
// with the linter scripts; both consume the same artifact files.

export interface RunYaml {
  run_id?: string;
  domain?: string;
  target_venue?: { name?: string; track?: string; source_url?: string };
  budget?: { gpu_hours?: number; hardware?: string; wall_clock_days?: number };
  deadline?: string;
  mode?: string;
  [key: string]: unknown;
}

export interface BibEntry {
  key: string;
  entry_type: string;
  title?: string;
  author?: string;
  year?: string;
  doi?: string;
  arxiv_id?: string;
  s2_paper_id?: string;
  [field: string]: string | undefined;
}

export interface ClaimsLedgerEntry {
  schema_version: 2;
  claim_id: string;
  value: number;
  unit?: string;
  metric?: string;
  config_name?: string | null;
  seed?: number | null;
  paper_tex_locator: string;
  source: string;
}

export interface ResultsRow {
  run_id?: string;
  config_name?: string;
  seed?: number;
  git_commit?: string;
  gpu_hours?: number;
  primary_metric?: number | string;
  event_flags?: string;
  notes?: string;
  [col: string]: unknown;
}

export interface ResultsSummary {
  [config: string]: {
    [metric: string]: { mean?: number; std?: number } | number | unknown;
  };
}

export interface PoolEntry {
  cite_key?: string;
  bibtex_key?: string;
  s2_paper_id?: string;
  arxiv_id?: string;
  doi?: string;
  title?: string;
  abstract?: string;
  authors?: string[];
  year?: number;
}

export type LintCounts = Record<string, Record<string, number>>;

export interface LintHeader {
  schema?: string;
  generated_at?: string;
  paper?: string;
  linters_run?: string[];
  exit_code?: number;
  counts?: LintCounts;
}

export interface LintFinding {
  rule: string;            // e.g. "citation-relevance" | "number-provenance"
  locator: string;         // "paper.tex:L42:C8"
  line: number;
  col: number;
  message: string;
  context?: string;
  extras: Record<string, string>;
}

export interface LintReport {
  raw: string;
  header: LintHeader;
  findings: LintFinding[];
  byLine: Record<number, LintFinding[]>;
}

export interface RunBundle {
  run: RunYaml | null;
  paperTex: string | null;
  bib: BibEntry[];
  claims: ClaimsLedgerEntry[];
  results: { rows: ResultsRow[]; summary: ResultsSummary | null };
  pool: PoolEntry[];
  lintReport: LintReport | null;
  fixtureName?: string;
  warnings: string[];
}

export type ClaimStatus =
  | "verified"
  | "verified-prior-work"
  | "untraced"
  | "unknown";

export interface Selection {
  kind: "number" | "cite" | "none";
  // When kind === "number":
  value?: number;
  raw?: string;
  locator?: string;
  status?: ClaimStatus;
  ledgerEntry?: ClaimsLedgerEntry;
  matchedRows?: ResultsRow[];
  // When kind === "cite":
  citeKey?: string;
  poolEntry?: PoolEntry;
  bibEntry?: BibEntry;
}
