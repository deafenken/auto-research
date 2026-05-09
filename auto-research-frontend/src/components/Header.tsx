import type { LintHeader, RunYaml } from "../data/types";

interface Props {
  run: RunYaml | null;
  fixtureName?: string;
  lintHeader?: LintHeader;
  warnings: string[];
}

function gpuHoursLabel(run: RunYaml | null): string {
  const used = (run as { gpu_hours_consumed_so_far?: number } | null)
    ?.gpu_hours_consumed_so_far;
  const budget = run?.budget?.gpu_hours;
  if (used != null && budget != null) {
    return `${used.toFixed(1)} / ${budget} GPU-h`;
  }
  if (budget != null) return `budget ${budget} GPU-h`;
  return "GPU-hours unknown";
}

export function Header({ run, fixtureName, lintHeader, warnings }: Props) {
  const counts = lintHeader?.counts ?? {};
  const exit = lintHeader?.exit_code;
  return (
    <header className="ar-header">
      <div className="ar-header__title">
        <span className="ar-header__id">{run?.run_id ?? fixtureName ?? "(no run.yaml)"}</span>
        <span className="ar-header__venue">
          {run?.target_venue?.name ?? ""} {run?.target_venue?.track ?? ""}
        </span>
      </div>
      <div className="ar-header__metrics">
        <span title="GPU hours used vs. budget">{gpuHoursLabel(run)}</span>
        {run?.deadline && <span>deadline {run.deadline}</span>}
        {fixtureName && <span className="ar-header__chip">fixture: {fixtureName}</span>}
      </div>
      <div className="ar-header__lint">
        {exit == null ? (
          <span className="ar-pill ar-pill--neutral">no lint report</span>
        ) : exit === 0 ? (
          <span className="ar-pill ar-pill--ok">lint OK</span>
        ) : (
          <span className="ar-pill ar-pill--bad">lint exit {exit}</span>
        )}
        {Object.entries(counts).map(([section, table]) => (
          <span key={section} className="ar-header__counts">
            {section}:
            {Object.entries(table).map(([label, n]) => (
              <code key={label}> {label}={n}</code>
            ))}
          </span>
        ))}
      </div>
      {warnings.length > 0 && (
        <ul className="ar-header__warnings">
          {warnings.map((w, i) => <li key={i}>{w}</li>)}
        </ul>
      )}
    </header>
  );
}
