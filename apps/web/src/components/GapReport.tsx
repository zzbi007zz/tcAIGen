"use client";
import type { MergeResult } from "../lib/api-client";

export default function GapReport({ mergeResult }: { mergeResult: MergeResult | null }) {
  if (!mergeResult) return null;
  if (mergeResult.gaps.length === 0) {
    return <div className="card"><h2>Gap Report</h2><p className="muted">No gaps detected.</p></div>;
  }
  return (
    <div className="card">
      <h2>Gap Report ({mergeResult.gaps.length})</h2>
      <ul>
        {mergeResult.gaps.map((gap, i) => (
          <li key={i} style={{ marginBottom: "0.5rem", listStyle: "none" }}>
            <span className="badge gap">{gap.gap_type}</span>{" "}
            <strong>{gap.subject_id}</strong> — {gap.note}
          </li>
        ))}
      </ul>
    </div>
  );
}
