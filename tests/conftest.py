import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.models import RequirementsDocument, TestCaseSet  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class MockGeminiClient:
    """Deterministic stand-in for GeminiClient in tests."""

    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []
        self.model = "mock-gemini"
        self.available = True

    def generate_content(self, prompt, image=None):
        self.calls.append(prompt)
        if not self.responses:
            raise AssertionError("MockGeminiClient has no responses queued")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def mock_gemini_client():
    return MockGeminiClient


@pytest.fixture
def sample_requirements_doc() -> RequirementsDocument:
    return RequirementsDocument.model_validate_json(
        (FIXTURES / "sample_requirements.json").read_text()
    )


@pytest.fixture
def sample_test_case_set() -> TestCaseSet:
    return TestCaseSet.model_validate_json(
        (FIXTURES / "sample_test_cases.json").read_text()
    )


@pytest.fixture
def sample_ba_text() -> str:
    return (FIXTURES / "sample_ba_doc.txt").read_text()


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES
