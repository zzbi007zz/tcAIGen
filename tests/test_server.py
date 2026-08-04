import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from apps.api.models import UIInventory
from apps.api.server import JOBS, app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_prompts_listing():
    names = client.get("/prompts").json()["prompts"]
    assert "extraction_v1.md" in names


def test_merge_endpoint(sample_requirements_doc):
    payload = {"requirements": json.loads(sample_requirements_doc.model_dump_json()),
               "ui_inventory": UIInventory().model_dump()}
    response = client.post("/merge", json=payload)
    assert response.status_code == 200
    assert "gaps" in response.json()


def test_extract_endpoint_invalid_extension():
    response = client.post(
        "/extract", files={"file": ("bad.csv", b"a,b", "text/csv")})
    assert response.status_code == 400


def test_generate_endpoint_returns_job(fixtures_dir):
    content = (fixtures_dir / "sample_ba_doc.txt").read_bytes()
    response = client.post(
        "/generate", files={"file": ("doc.txt", content, "text/plain")})
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    assert job_id in JOBS


def test_status_polling_unknown_job():
    assert client.get("/status/unknown").status_code == 404


def test_status_after_generate(fixtures_dir):
    content = (fixtures_dir / "sample_ba_doc.txt").read_bytes()
    job_id = client.post(
        "/generate", files={"file": ("doc.txt", content, "text/plain")}).json()["job_id"]
    status = client.get(f"/status/{job_id}").json()
    assert status["status"] in ("processing", "complete", "error")


def test_export_before_completion_conflict():
    JOBS["j1"] = {"status": "processing", "progress": 0.1,
                  "result": None, "quality_report": None, "error": None}
    assert client.get("/export/j1/gherkin").status_code == 409


def test_gherkin_export(sample_test_case_set, sample_requirements_doc):
    JOBS["j2"] = {"status": "complete", "progress": 1.0, "result": sample_test_case_set,
                  "requirements": sample_requirements_doc,
                  "quality_report": None, "error": None}
    response = client.get("/export/j2/gherkin")
    assert response.status_code == 200
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    assert any(name.endswith(".feature") for name in archive.namelist())


def test_xlsx_export(sample_test_case_set):
    pytest.importorskip("openpyxl")
    JOBS["j3"] = {"status": "complete", "progress": 1.0, "result": sample_test_case_set,
                  "requirements": None, "quality_report": None, "error": None}
    response = client.get("/export/j3/xlsx")
    assert response.status_code == 200
    assert response.content[:2] == b"PK"
