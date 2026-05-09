import type {
  BibEntry,
  PoolEntry,
  ResultsRow,
  ResultsSummary,
  Selection,
} from "../data/types";

interface Props {
  selection: Selection;
  rows: ResultsRow[];
  summary: ResultsSummary | null;
  pool: PoolEntry[];
  bib: BibEntry[];
}

function findRowsByValue(value: number, rows: ResultsRow[],
                         tolerance = 0.005): ResultsRow[] {
  const out: ResultsRow[] = [];
  for (const row of rows) {
    for (const cell of Object.values(row)) {
      if (typeof cell === "number" && Math.abs(cell - value) <= tolerance) {
        out.push(row);
        break;
      }
    }
  }
  return out;
}

function searchSummary(value: number, summary: ResultsSummary | null,
                        tolerance = 0.005): { path: string; mean: number }[] {
  if (!summary) return [];
  const hits: { path: string; mean: number }[] = [];
  const walk = (node: unknown, path: string) => {
    if (node && typeof node === "object" && !Array.isArray(node)) {
      for (const [k, v] of Object.entries(node)) walk(v, path ? `${path}.${k}` : k);
    } else if (typeof node === "number"
               && Math.abs(node - value) <= tolerance) {
      hits.push({ path, mean: node });
    }
  };
  walk(summary, "");
  return hits;
}

function findPoolEntry(key: string | undefined,
                        pool: PoolEntry[],
                        bib: BibEntry[]): PoolEntry | undefined {
  if (!key) return undefined;
  const direct = pool.find((p) =>
    p.cite_key === key || p.bibtex_key === key);
  if (direct) return direct;
  const bibEntry = bib.find((b) => b.key === key);
  if (!bibEntry) return undefined;
  return pool.find((p) =>
    (bibEntry.s2_paper_id && p.s2_paper_id === bibEntry.s2_paper_id) ||
    (bibEntry.arxiv_id && p.arxiv_id === bibEntry.arxiv_id) ||
    (bibEntry.doi && p.doi === bibEntry.doi));
}

function CsvRowView({ rows }: { rows: ResultsRow[] }) {
  if (rows.length === 0) return <p>No matching row in results.csv.</p>;
  const cols = Object.keys(rows[0]);
  return (
    <table className="ar-rows">
      <thead>
        <tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            {cols.map((c) => <td key={c}>{String(row[c] ?? "")}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function NumberView({ selection, rows, summary }: {
  selection: Selection; rows: ResultsRow[]; summary: ResultsSummary | null;
}) {
  if (selection.value == null) return null;
  const ledger = selection.ledgerEntry;
  const summaryHits = searchSummary(selection.value, summary);
  const csvRows = findRowsByValue(selection.value, rows);
  return (
    <div>
      <h3>Number {selection.raw}</h3>
      <p className={`ar-status ar-status--${selection.status}`}>
        {selection.status?.toUpperCase()}
      </p>
      {ledger && (
        <section>
          <h4>Claim ledger</h4>
          <ul>
            <li><b>id:</b> {ledger.claim_id}</li>
            <li><b>metric:</b> {ledger.metric ?? "—"} {ledger.unit ? `(${ledger.unit})` : ""}</li>
            <li><b>config:</b> {String(ledger.config_name ?? "—")}</li>
            <li><b>seed:</b> {ledger.seed == null ? "—" : ledger.seed}</li>
            <li><b>locator:</b> <code>{ledger.paper_tex_locator}</code></li>
            <li><b>source:</b> <code>{ledger.source}</code></li>
          </ul>
        </section>
      )}
      {summaryHits.length > 0 && (
        <section>
          <h4>results_summary.json</h4>
          <ul>
            {summaryHits.map((h) => (
              <li key={h.path}><code>{h.path}</code> = {h.mean}</li>
            ))}
          </ul>
        </section>
      )}
      <section>
        <h4>results.csv (within ±0.005)</h4>
        <CsvRowView rows={csvRows} />
      </section>
    </div>
  );
}

function CiteView({ selection, pool, bib }: {
  selection: Selection; pool: PoolEntry[]; bib: BibEntry[];
}) {
  const bibEntry = bib.find((b) => b.key === selection.citeKey);
  const poolEntry = findPoolEntry(selection.citeKey, pool, bib);
  return (
    <div>
      <h3>Citation {selection.citeKey}</h3>
      {!poolEntry && (
        <p className="ar-status ar-status--untraced">
          Not in literature_pool.json — fails Rule 2 (Layer 1–3 unverified).
        </p>
      )}
      {bibEntry && (
        <section>
          <h4>references.bib</h4>
          <ul>
            {Object.entries(bibEntry).map(([k, v]) =>
              <li key={k}><b>{k}:</b> {String(v)}</li>
            )}
          </ul>
        </section>
      )}
      {poolEntry && (
        <section>
          <h4>literature_pool.json</h4>
          <p><b>{poolEntry.title}</b></p>
          {poolEntry.abstract && <p style={{ whiteSpace: "pre-wrap" }}>{poolEntry.abstract}</p>}
          <ul>
            {poolEntry.s2_paper_id && <li>S2: <code>{poolEntry.s2_paper_id}</code></li>}
            {poolEntry.arxiv_id && <li>arXiv: <code>{poolEntry.arxiv_id}</code></li>}
            {poolEntry.doi && <li>DOI: <code>{poolEntry.doi}</code></li>}
          </ul>
        </section>
      )}
    </div>
  );
}

export function EvidencePane({ selection, rows, summary, pool, bib }: Props) {
  if (selection.kind === "none") {
    return <div className="ar-evidence ar-evidence--empty">
      Click a highlighted number or citation to see its evidence.
    </div>;
  }
  if (selection.kind === "number") {
    return <div className="ar-evidence">
      <NumberView selection={selection} rows={rows} summary={summary} />
    </div>;
  }
  return <div className="ar-evidence">
    <CiteView selection={selection} pool={pool} bib={bib} />
  </div>;
}
