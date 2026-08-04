"""FastAPI server exposing the full test case generation pipeline."""
from __future__ import annotations

import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from apps.api.evals.metrics import evaluate_all
from apps.api.models import MergeResult, RequirementsDocument, UIInventory
from apps.api.pipeline import extract, ingest, merge, vision
from apps.api.pipeline.export import gherkin_writer, xlsx_writer
from apps.api.pipeline.loop import Loop

MAX_DOC_BYTES = 10 * 1024 * 1024
MAX_IMAGE_BYTES = 5 * 1024 * 1024

app = FastAPI(title="BDD Test Case Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS: Dict[str, Dict[str, Any]] = {}


class MergeRequest(BaseModel):
    requirements: RequirementsDocument
    ui_inventory: UIInventory


def _save_upload(upload: UploadFile, data: bytes) -> Path:
    path = Path(tempfile.mkdtemp()) / (upload.filename or "upload.bin")
    path.write_bytes(data)
    return path


async def _read_upload(upload: UploadFile, limit: int) -> bytes:
    data = await upload.read()
    if len(data) > limit:
        raise HTTPException(status_code=413, detail="File too large")
    return data


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/prompts")
def list_prompts() -> Dict[str, List[str]]:
    prompts_dir = Path(__file__).resolve().parent / "prompts"
    return {"prompts": sorted(p.name for p in prompts_dir.glob("*.md"))}


@app.post("/extract")
async def extract_endpoint(file: UploadFile = File(...)) -> Any:
    data = await _read_upload(file, MAX_DOC_BYTES)
    path = _save_upload(file, data)
    try:
        return extract.run_extraction(path)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/vision")
async def vision_endpoint(files: List[UploadFile] = File(...)) -> Any:
    paths = []
    for upload in files:
        data = await _read_upload(upload, MAX_IMAGE_BYTES)
        paths.append(_save_upload(upload, data))
    try:
        return vision.run_vision_pipeline(paths)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/merge")
def merge_endpoint(payload: MergeRequest) -> MergeResult:
    return merge.merge_and_analyze(payload.requirements, payload.ui_inventory)


def _run_job(job_id: str, doc_path: Path, screenshot_paths: List[Path] | None = None) -> None:
    job = JOBS[job_id]
    try:
        job["progress"] = 0.15
        requirements = extract.run_extraction(doc_path)
        job["requirements"] = requirements
        job["progress"] = 0.30

        if screenshot_paths:
            job["progress"] = 0.45
            inventory = vision.run_vision_pipeline(screenshot_paths)
            merge_result = merge.merge_and_analyze(requirements, inventory)
            job["merge_result"] = merge_result

        job["progress"] = 0.55
        loop = Loop()
        result = loop.run(requirements, source=ingest.parse_document(doc_path))
        job["progress"] = 0.85
        if result.final_output:
            from apps.api.models import TestCaseSet

            test_cases = TestCaseSet.model_validate(result.final_output)
            job["result"] = test_cases
            job["quality_report"] = evaluate_all(
                test_cases, requirements, source=ingest.parse_document(doc_path)
            )
        job["loop_passed"] = result.passed
        job["status"] = "complete"
        job["progress"] = 1.0
    except Exception as exc:  # surface pipeline errors to status endpoint
        job["status"] = "error"
        job["error"] = str(exc)


@app.post("/generate")
async def generate_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    screenshots: Optional[List[UploadFile]] = File(None),
) -> Dict[str, str]:
    data = await _read_upload(file, MAX_DOC_BYTES)
    path = _save_upload(file, data)
    shot_paths: List[Path] = []
    if screenshots:
        for shot in screenshots:
            shot_data = await _read_upload(shot, MAX_IMAGE_BYTES)
            shot_paths.append(_save_upload(shot, shot_data))
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {
        "status": "processing", "progress": 0.0,
        "result": None, "quality_report": None, "merge_result": None, "error": None,
    }
    background_tasks.add_task(_run_job, job_id, path, shot_paths or None)
    return {"job_id": job_id}


@app.get("/status/{job_id}")
def status_endpoint(job_id: str) -> Dict[str, Any]:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return {
        "status": job["status"],
        "progress": job["progress"],
        "error": job["error"],
        "result": job["result"],
        "quality_report": job["quality_report"],
        "merge_result": job.get("merge_result"),
    }


def _job_test_cases(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    if job["result"] is None:
        raise HTTPException(status_code=409, detail="Job has no results yet")
    return job


@app.get("/export/{job_id}/gherkin")
def export_gherkin(job_id: str) -> FileResponse:
    job = _job_test_cases(job_id)
    out_dir = Path(tempfile.mkdtemp())
    names = {f.id: f.name for f in (job.get("requirements").features if job.get("requirements") else [])}
    gherkin_writer.write_feature_file(job["result"], out_dir, feature_names=names)
    zip_path = out_dir / "features.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for feature_file in out_dir.glob("*.feature"):
            archive.write(feature_file, arcname=feature_file.name)
    return FileResponse(str(zip_path), filename="features.zip")


@app.get("/export/{job_id}/xlsx")
def export_xlsx(job_id: str) -> FileResponse:
    job = _job_test_cases(job_id)
    out_path = Path(tempfile.mkdtemp()) / "test_cases.xlsx"
    xlsx_writer.write_test_cases_xlsx(job["result"], out_path)
    return FileResponse(str(out_path), filename="test_cases.xlsx")
