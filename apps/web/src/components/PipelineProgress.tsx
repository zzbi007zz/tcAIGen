"use client";

const STEPS = ["Uploading", "Extracting", "Merging", "Generating", "Verifying"];

export default function PipelineProgress({ progress }: { progress: number }) {
  const activeIndex = Math.min(STEPS.length - 1, Math.floor(progress * STEPS.length));
  return (
    <div className="steps">
      {STEPS.map((label, i) => (
        <div
          key={label}
          className={`step${i < activeIndex || progress >= 1 ? " done" : i === activeIndex ? " active" : ""}`}
        >
          {label}
        </div>
      ))}
    </div>
  );
}
