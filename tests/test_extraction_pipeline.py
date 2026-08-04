import json

import pytest

from apps.api.models import RequirementsDocument
from apps.api.pipeline import extract, ingest
from tests.conftest import MockGeminiClient


def extraction_payload(title="Extracted Doc"):
    return json.dumps({
        "meta": {"title": title, "source_type": "paste"},
        "features": [{
            "id": "F1", "name": "Login", "description": "Login feature",
            "source_location": "Section 1",
            "acceptance_criteria": [
                {"id": "AC1", "text": "Valid login", "grounding": "explicit",
                 "source_location": "Section 1.1", "validations": []},
                {"id": "AC2", "text": "Session timeout", "grounding": "inferred",
                 "source_location": "Section 1.2", "validations": []},
            ],
        }],
        "confidence": {"explicit_criteria_count": 1, "inferred_criteria_count": 1,
                       "low_confidence_features": []},
    })


class TestIngest:
    def test_source_type_mapping(self):
        assert ingest.source_type_for("a.txt") == "paste"
        assert ingest.source_type_for("a.docx") == "word"
        assert ingest.source_type_for("a.pdf") == "pdf"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            ingest.parse_document("/nonexistent/doc.txt")

    def test_unsupported_extension(self, tmp_path):
        p = tmp_path / "x.csv"
        p.write_text("a,b")
        with pytest.raises(ValueError):
            ingest.parse_document(p)

    def test_parses_txt(self, fixtures_dir):
        text = ingest.parse_document(fixtures_dir / "sample_ba_doc.txt")
        assert "User Authentication Module" in text

    def test_parses_docx(self, fixtures_dir):
        pytest.importorskip("docx")
        text = ingest.parse_document(fixtures_dir / "sample_ba_doc.docx")
        assert "User Authentication Module" in text


class TestFencesAndTitle:
    def test_strips_fences(self):
        assert extract.strip_markdown_fences("```json\n{\"a\":1}\n```") == '{"a":1}'

    def test_strips_plain_fences(self):
        assert extract.strip_markdown_fences("```\nx\n```") == "x"

    def test_no_fences(self):
        assert extract.strip_markdown_fences('{"a":1}') == '{"a":1}'

    def test_extracts_heading(self):
        assert extract.extract_title("# My Title\nbody") == "My Title"

    def test_extracts_first_line_no_heading(self):
        assert extract.extract_title("Plain title\nbody") == "Plain title"

    def test_empty_text(self):
        assert extract.extract_title("") == "Untitled Document"


class TestPromptLoading:
    def test_load_prompt(self):
        assert "{document_text}" in extract.load_prompt("v1")

    def test_prompt_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            extract.load_prompt("v99")

    def test_fills_template(self):
        assert "HELLO" in extract.fill_template("X {document_text} Y", "HELLO")


class TestRunExtraction:
    def test_parses_valid_json(self, fixtures_dir):
        client = MockGeminiClient([extraction_payload()])
        doc = extract.run_extraction(fixtures_dir / "sample_ba_doc.txt", client=client)
        assert isinstance(doc, RequirementsDocument)
        assert doc.features[0].id == "F1"
        assert doc.confidence.explicit_criteria_count == 1
        assert doc.confidence.inferred_criteria_count == 1

    def test_retries_on_json_error(self, fixtures_dir):
        client = MockGeminiClient(["not json", extraction_payload()])
        doc = extract.run_extraction(fixtures_dir / "sample_ba_doc.txt", client=client)
        assert doc.meta.title == "Extracted Doc"
        assert len(client.calls) == 2

    def test_raises_after_max_failures(self, fixtures_dir):
        client = MockGeminiClient(["bad", "bad", "bad"])
        with pytest.raises(ValueError, match="failed after 3 attempts"):
            extract.run_extraction(fixtures_dir / "sample_ba_doc.txt", client=client)

    def test_end_to_end(self, fixtures_dir):
        client = MockGeminiClient(["```json\n" + extraction_payload() + "\n```"])
        doc = extract.run_extraction(fixtures_dir / "sample_ba_doc.txt", client=client)
        assert doc.meta.source_type.value == "paste"
