import json

import pytest

from apps.api.models import TestCaseSet
from apps.api.pipeline import generate
from tests.conftest import MockGeminiClient


def generation_payload():
    return json.dumps({
        "source_doc_title": "Doc",
        "test_cases": [
            {"tc_id": "TC-1", "feature_id": "F1", "title": "Valid login", "category": "positive",
             "priority": "high", "grounding_source": "AC1: valid login works",
             "gherkin": {"scenario_type": "scenario", "title": "Login works", "tags": ["@positive"],
                         "steps": [{"keyword": "Given", "text": "a registered user"},
                                   {"keyword": "When", "text": "the user submits valid credentials"},
                                   {"keyword": "Then", "text": "access is granted"}],
                         "examples_table": None}},
            {"tc_id": "TC-2", "feature_id": "F1", "title": "Password boundaries", "category": "boundary",
             "priority": "medium", "grounding_source": "AC2: password 8-64 chars",
             "gherkin": {"scenario_type": "scenario_outline", "title": "Password length", "tags": ["@boundary"],
                         "steps": [{"keyword": "Given", "text": "the registration form"},
                                   {"keyword": "When", "text": "the user enters a <length> char password"},
                                   {"keyword": "Then", "text": "it is <result>"}],
                         "examples_table": [{"length": "7", "result": "rejected"},
                                            {"length": "8", "result": "accepted"}]}},
        ],
    })


class TestPrompt:
    def test_loads_prompt(self):
        assert "{requirements_json}" in generate.load_generation_prompt("v1")

    def test_prompt_has_source_document_placeholder(self):
        assert "{source_document}" in generate.load_generation_prompt("v1")

    def test_build_feature_content(self, sample_requirements_doc):
        content = json.loads(generate.build_feature_content(sample_requirements_doc))
        assert content["features"][0]["id"] == "F-REG"


class TestRunGeneration:
    def test_generates_valid_output(self, sample_requirements_doc):
        client = MockGeminiClient([generation_payload()])
        result = generate.run_generation(sample_requirements_doc, client=client)
        assert isinstance(result, TestCaseSet)
        assert len(result.test_cases) == 2

    def test_scenario(self, sample_requirements_doc):
        result = generate.run_generation(sample_requirements_doc, client=MockGeminiClient([generation_payload()]))
        assert result.test_cases[0].gherkin.scenario_type.value == "scenario"

    def test_scenario_outline(self, sample_requirements_doc):
        result = generate.run_generation(sample_requirements_doc, client=MockGeminiClient([generation_payload()]))
        outline = result.test_cases[1]
        assert outline.gherkin.scenario_type.value == "scenario_outline"
        assert len(outline.gherkin.examples_table) == 2

    def test_rejects_missing_grounding(self, sample_requirements_doc):
        payload = json.loads(generation_payload())
        payload["test_cases"][0]["grounding_source"] = ""
        client = MockGeminiClient([json.dumps(payload)] * 3)
        with pytest.raises(ValueError, match="grounding"):
            generate.run_generation(sample_requirements_doc, client=client)

    def test_retries_on_bad_json(self, sample_requirements_doc):
        client = MockGeminiClient(["broken", generation_payload()])
        result = generate.run_generation(sample_requirements_doc, client=client)
        assert len(client.calls) == 2
        assert len(result.test_cases) == 2

    def test_source_text_injected_into_prompt(self, sample_requirements_doc):
        client = MockGeminiClient([generation_payload()])
        generate.run_generation(
            sample_requirements_doc, client=client, source_text="RAW SOURCE MARKER")
        assert "RAW SOURCE MARKER" in client.calls[0]
        assert "{source_document}" not in client.calls[0]


class TestGherkinValidation:
    def test_valid_gherkin(self, sample_test_case_set):
        assert generate.validate_gherkin(sample_test_case_set) == []

    def test_invalid_gherkin(self, sample_test_case_set):
        sample_test_case_set.test_cases[0].gherkin.steps = []
        sample_test_case_set.test_cases[0].gherkin.title = ""
        failures = generate.validate_gherkin(sample_test_case_set)
        assert sample_test_case_set.test_cases[0].tc_id in failures

    def test_scenario_outline_valid(self, sample_test_case_set):
        outlines = [tc for tc in sample_test_case_set.test_cases
                    if tc.gherkin.scenario_type.value == "scenario_outline"]
        assert outlines and all(
            tc.gherkin.examples_table for tc in outlines)
