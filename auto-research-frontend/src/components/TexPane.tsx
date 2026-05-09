import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { tokenize, type Token } from "../data/tex_tokenize";
import type {
  ClaimStatus,
  ClaimsLedgerEntry,
  LintReport,
  Selection,
} from "../data/types";

interface Props {
  paperTex: string;
  lint: LintReport | null;
  ledger: ClaimsLedgerEntry[];
  onSelect: (sel: Selection) => void;
  selectedLocator?: string;
}

function statusFromLint(line: number, lint: LintReport | null): ClaimStatus {
  if (!lint) return "unknown";
  const findings = lint.byLine[line];
  if (!findings) return "verified";  // no findings on this line ⇒ presumed verified
  if (findings.some((f) => f.rule === "number-provenance"
                            && f.message.includes("UNTRACED"))) {
    return "untraced";
  }
  return "verified";
}

function ledgerLookup(value: number, line: number,
                       ledger: ClaimsLedgerEntry[]): ClaimsLedgerEntry | undefined {
  return ledger.find((entry) => {
    if (Math.abs(entry.value - value) > 0.005) return false;
    const m = /:L(\d+)/.exec(entry.paper_tex_locator);
    if (!m) return false;
    return Number(m[1]) === line;
  });
}

function priorWorkStatus(token: Extract<Token, { kind: "number" }>,
                          lint: LintReport | null): boolean {
  if (!lint) return false;
  const findings = lint.byLine[token.line] ?? [];
  return findings.some((f) =>
    f.message.includes("VERIFIED-PRIOR-WORK"));
}

export function TexPane({ paperTex, lint, ledger, onSelect, selectedLocator }: Props) {
  const tokens = useMemo(() => tokenize(paperTex), [paperTex]);

  const numberClass = (t: Extract<Token, { kind: "number" }>) => {
    const ledgerHit = ledgerLookup(t.value, t.line, ledger);
    const status: ClaimStatus = ledgerHit
      ? "verified"
      : priorWorkStatus(t, lint)
      ? "verified-prior-work"
      : statusFromLint(t.line, lint);
    return { status, ledgerHit };
  };

  return (
    <pre className="ar-tex-pane" aria-label="paper.tex">
      {tokens.map((t, i) => {
        if (t.kind === "text") return <span key={i}>{t.text}</span>;
        if (t.kind === "math") {
          let html = "";
          try {
            html = katex.renderToString(t.tex, {
              throwOnError: false,
              displayMode: t.display,
            });
          } catch {
            html = t.tex;
          }
          return (
            <span
              key={i}
              className={t.display ? "ar-math ar-math--display" : "ar-math"}
              dangerouslySetInnerHTML={{ __html: html }}
            />
          );
        }
        if (t.kind === "cite") {
          const locator = `paper.tex:L${t.line}:C${t.col}`;
          const cls = "ar-cite" + (selectedLocator === locator ? " ar-cite--selected" : "");
          return (
            <span
              key={i}
              className={cls}
              tabIndex={0}
              role="button"
              onClick={() => onSelect({
                kind: "cite",
                citeKey: t.keys[0],
                locator,
                raw: t.raw,
              })}
            >
              [{t.keys.join(",")}]
            </span>
          );
        }
        // number
        const { status, ledgerHit } = numberClass(t);
        const locator = `paper.tex:L${t.line}:C${t.col}`;
        const cls =
          "ar-claim ar-claim--" + status +
          (selectedLocator === locator ? " ar-claim--selected" : "");
        return (
          <span
            key={i}
            className={cls}
            tabIndex={0}
            role="button"
            title={`${t.raw} — ${status}`}
            onClick={() => onSelect({
              kind: "number",
              value: t.value,
              raw: t.raw,
              locator,
              status,
              ledgerEntry: ledgerHit,
            })}
          >
            {t.raw}
          </span>
        );
      })}
    </pre>
  );
}
