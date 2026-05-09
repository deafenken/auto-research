import { useEffect, useState } from "react";
import { Header } from "./components/Header";
import { TexPane } from "./components/TexPane";
import { EvidencePane } from "./components/EvidencePane";
import { fetchBundle } from "./data/loader";
import type { RunBundle, Selection } from "./data/types";
import "./styles/inspector.css";

function fixtureFromUrl(): string | undefined {
  if (typeof window === "undefined") return undefined;
  const params = new URLSearchParams(window.location.search);
  return params.get("fixture") ?? undefined;
}

export function App() {
  const [bundle, setBundle] = useState<RunBundle | null>(null);
  const [selection, setSelection] = useState<Selection>({ kind: "none" });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBundle({ fixture: fixtureFromUrl() })
      .then((b) => setBundle(b))
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="ar-error">Failed to load bundle: {error}</div>;
  if (!bundle) return <div className="ar-loading">Loading run bundle…</div>;

  const lintHeader = bundle.lintReport?.header;
  return (
    <div className="ar-app">
      <Header
        run={bundle.run}
        fixtureName={bundle.fixtureName}
        lintHeader={lintHeader}
        warnings={bundle.warnings}
      />
      <main className="ar-inspector">
        <section className="ar-inspector__left">
          {bundle.paperTex ? (
            <TexPane
              paperTex={bundle.paperTex}
              lint={bundle.lintReport}
              ledger={bundle.claims}
              onSelect={setSelection}
              selectedLocator={selection.locator}
            />
          ) : (
            <p>paper.tex not available — nothing to inspect.</p>
          )}
        </section>
        <section className="ar-inspector__right">
          <EvidencePane
            selection={selection}
            rows={bundle.results.rows}
            summary={bundle.results.summary}
            pool={bundle.pool}
            bib={bundle.bib}
          />
        </section>
      </main>
    </div>
  );
}
