"""CLI demo: process a BA doc end-to-end without the server."""
from __future__ import annotations

import os

# Only load .env when NOT running under pytest
if not os.environ.get("PYTEST_CURRENT_TEST"):
    from dotenv import load_dotenv

    load_dotenv()

import argparse
import sys
import time
from pathlib import Path

from apps.api.evals.metrics import evaluate_all, gate
from apps.api.pipeline import extract, generate, ingest, merge, vision
from apps.api.pipeline.export import gherkin_writer


def run(doc_path: str, screenshots: str | None = None, output: str = "output", verbose: bool = False) -> int:
    start = time.time()
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[1/5] Extracting requirements...")
    requirements = extract.run_extraction(doc_path)
    if verbose:
        print(f"      {len(requirements.features)} features extracted")

    merge_result = None
    if screenshots:
        print("[2/5] Analyzing screenshots...")
        paths = sorted(Path(screenshots).glob("*"))
        inventory = vision.run_vision_pipeline(paths)
        merge_result = merge.merge_and_analyze(requirements, inventory)
        if merge_result.gaps:
            print("      Gaps detected:")
            for gap in merge_result.gaps:
                print(f"      - [{gap.gap_type.value}] {gap.note}")
    else:
        print("[2/5] No screenshots provided — skipping vision/merge")

    print("[3/5] Generating test cases...")
    test_cases = generate.run_generation(requirements)

    print("[4/5] Running deterministic gate...")
    gate_result = gate(test_cases)
    print(f"      gate: {'PASS' if gate_result.passed else 'FAIL'}")

    print("[5/5] Writing outputs...")
    names = {f.id: f.name for f in requirements.features}
    written = gherkin_writer.write_feature_file(test_cases, out_dir, feature_names=names)
    report = evaluate_all(test_cases, requirements, source_doc=ingest.parse_document(doc_path))
    report_path = out_dir / "report.md"
    report_path.write_text(
        f"# Quality Report\n\nOverall score: {report.overall_score}/100\n\n"
        + "\n".join(f"- **{k}**: {v}" for k, v in report.breakdown.items())
        + "\n\n## Warnings\n"
        + ("\n".join(f"- [{w.metric}] {w.message}" for w in report.warnings) or "None")
        + f"\n\nElapsed: {time.time() - start:.1f}s\n",
        encoding="utf-8",
    )
    print(f"Done. {len(written)} feature file(s) + report in {out_dir}/ "
          f"(score {report.overall_score}/100, {time.time() - start:.1f}s)")
    return 0 if gate_result.passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="apps.cli", description="BDD test case generator CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("doc_path")
    run_parser.add_argument("--screenshots", default=None)
    run_parser.add_argument("--output", default="output")
    run_parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if args.command == "run":
        if not Path(args.doc_path).exists():
            print(f"error: file not found: {args.doc_path}", file=sys.stderr)
            return 2
        return run(args.doc_path, args.screenshots, args.output, args.verbose)
    return 2


if __name__ == "__main__":
    sys.exit(main())
