"use client";
import { useCallback, useRef, useState } from "react";
import ExportPanel from "../components/ExportPanel";
import FileUpload from "../components/FileUpload";
import GapReport from "../components/GapReport";
import PipelineProgress from "../components/PipelineProgress";
import QualityDashboard from "../components/QualityDashboard";
import TestCaseBrowser from "../components/TestCaseBrowser";
import { generate, pollStatus, type JobStatus, type MergeResult } from "../lib/api-client";

export default function Home() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mergeResult, setMergeResult] = useState<MergeResult | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const poll = useCallback((id: string) => {
    timer.current = setInterval(async () => {
      try {
        const next = await pollStatus(id);
        setStatus(next);
        if (next.merge_result) setMergeResult(next.merge_result);
        if (next.status !== "processing" && timer.current) {
          clearInterval(timer.current);
          if (next.status === "error") setError(next.error ?? "Pipeline failed");
        }
      } catch (e) {
        if (timer.current) clearInterval(timer.current);
        setError(e instanceof Error ? e.message : "Polling failed");
      }
    }, 1500);
  }, []);

  const onFile = useCallback(async (file: File, screenshots?: File[]) => {
    setError(null);
    setStatus(null);
    setJobId(null);
    setMergeResult(null);
    try {
      const { job_id } = await generate(file, screenshots);
      setJobId(job_id);
      setStatus({ status: "processing", progress: 0, error: null, result: null, quality_report: null, merge_result: null });
      poll(job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    }
  }, [poll]);

  const busy = status?.status === "processing";
  return (
    <main className="container">
      <h1>BDD Test Case Generator</h1>
      <div className="card">
        <FileUpload onFile={onFile} disabled={busy} />
        {error && <p className="error" style={{ marginTop: "0.75rem" }}>{error}</p>}
      </div>
      {busy && status && (
        <div className="card"><PipelineProgress progress={status.progress} /></div>
      )}
      {/* Gap report intentionally renders BEFORE test cases */}
      <GapReport mergeResult={mergeResult} />
      {status?.result && <TestCaseBrowser testCases={status.result.test_cases} />}
      <QualityDashboard report={status?.quality_report ?? null} />
      {status?.status === "complete" && <ExportPanel jobId={jobId} />}
    </main>
  );
}
