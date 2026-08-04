"use client";
import { useMemo, useState } from "react";
import type { TestCase } from "../lib/api-client";

type SortKey = "tc_id" | "category" | "priority";

export default function TestCaseBrowser({ testCases }: { testCases: TestCase[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("tc_id");
  const [category, setCategory] = useState("");
  const [feature, setFeature] = useState("");

  const features = useMemo(
    () => Array.from(new Set(testCases.map((tc) => tc.feature_id))), [testCases]
  );

  const rows = useMemo(() => {
    const filtered = testCases.filter(
      (tc) => (!category || tc.category === category) && (!feature || tc.feature_id === feature)
    );
    return [...filtered].sort((a, b) => a[sortKey].localeCompare(b[sortKey]));
  }, [testCases, sortKey, category, feature]);

  if (testCases.length === 0) {
    return <div className="card"><h2>Test Cases</h2><p className="muted">No test cases yet.</p></div>;
  }

  return (
    <div className="card">
      <h2>Test Cases ({rows.length})</h2>
      <div className="filters">
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {["positive", "negative", "edge", "boundary"].map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select value={feature} onChange={(e) => setFeature(e.target.value)}>
          <option value="">All features</option>
          {features.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>
      </div>
      <table>
        <thead>
          <tr>
            <th onClick={() => setSortKey("tc_id")}>ID</th>
            <th>Title</th>
            <th onClick={() => setSortKey("category")}>Category</th>
            <th onClick={() => setSortKey("priority")}>Priority</th>
            <th>Scenario</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((tc) => (
            <tr key={tc.tc_id}>
              <td>{tc.tc_id}</td>
              <td>{tc.title}</td>
              <td><span className={`badge ${tc.category}`}>{tc.category}</span></td>
              <td>{tc.priority}</td>
              <td>{tc.gherkin.title}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
