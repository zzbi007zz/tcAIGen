"use client";
import type { QualityReport } from "../lib/api-client";

function pct(value: unknown): number {
  const n = typeof value === "number" ? value : 0;
  return Math.round(n <= 1 ? n * 100 : n);
}

export default function QualityDashboard({ report }: { report: QualityReport | null }) {
  if (!report) return null;
  const metrics = Object.entries(report.breakdown).filter(([, v]) => typeof v === "number");
  return (
    <div className="card">
      <h2>Quality Report</h2>
      <div className="score">{report.overall_score}/100</div>
      {metrics.map(([name, value]) => (
        <div key={name} className="metric">
          <div className="muted">{name.replace(/_/g, " ")} — {pct(value)}%</div>
          <div className="metric-bar">
            <div className="metric-fill" style={{ width: `${pct(value)}%` }} />
          </div>
        </div>
      ))}
      {report.warnings.length > 0 && (
        <div style={{ marginTop: "1rem" }}>
          <h2>Warnings</h2>
          {report.warnings.map((w, i) => (
            <p key={i} className="muted">
              [{w.metric}] {w.message}
              {w.tc_ids.length > 0 && ` (${w.tc_ids.join(", ")})`}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
