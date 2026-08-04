"use client";
import { exportUrl } from "../lib/api-client";

export default function ExportPanel({ jobId }: { jobId: string | null }) {
  if (!jobId) return null;
  return (
    <div className="card">
      <h2>Export</h2>
      <a href={exportUrl(jobId, "gherkin")} style={{ marginRight: "0.75rem" }}>
        <button>Download .feature zip</button>
      </a>
      <a href={exportUrl(jobId, "xlsx")}>
        <button>Download .xlsx</button>
      </a>
    </div>
  );
}
