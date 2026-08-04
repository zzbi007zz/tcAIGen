const API = process.env.API_BASE_URL || "http://localhost:8000";

export interface JobStatus {
  status: "processing" | "complete" | "error";
  progress: number;
  error: string | null;
  result: { test_cases: TestCase[] } | null;
  quality_report: QualityReport | null;
  merge_result: MergeResult | null;
}

export interface TestCase {
  tc_id: string;
  feature_id: string;
  title: string;
  category: "positive" | "negative" | "edge" | "boundary";
  priority: string;
  grounding_source: string;
  gherkin: {
    scenario_type: string;
    title: string;
    tags: string[];
    steps: { keyword: string; text: string }[];
    examples_table: Record<string, string>[] | null;
  };
}

export interface QualityReport {
  overall_score: number;
  breakdown: Record<string, unknown>;
  warnings: { metric: string; message: string; tc_ids: string[] }[];
}

export interface MergeResult {
  mappings: { feature_id: string; screen_id: string; similarity_score: number }[];
  gaps: { gap_type: string; subject_id: string; note: string; severity: string }[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const generate = (file: File, screenshots?: File[]) => {
  const form = new FormData();
  form.append("file", file);
  if (screenshots) {
    for (const shot of screenshots) {
      form.append("screenshots", shot);
    }
  }
  return request<{ job_id: string }>("/generate", { method: "POST", body: form });
};

export const pollStatus = (jobId: string) => request<JobStatus>(`/status/${jobId}`);

export const merge = (requirements: unknown, uiInventory: unknown) =>
  request<MergeResult>("/merge", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ requirements, ui_inventory: uiInventory }),
  });

export const exportUrl = (jobId: string, kind: "gherkin" | "xlsx") =>
  `${API}/export/${jobId}/${kind}`;
