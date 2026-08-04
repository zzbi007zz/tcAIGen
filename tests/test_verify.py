import json

import pytest

from apps.api.pipeline import verify


class MockVerifierClient:
    model = "claude-mock"
    available = True

    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def generate_content(self, prompt):
        self.prompts.append(prompt)
        return self.responses.pop(0)


def verdict_payload(passed=True, confidence=0.9):
    return json.dumps({"passed": passed, "confidence": confidence,
                       "failed_criteria": [], "feedback": None})


def test_load_verify_prompt():
    prompt = verify.load_verify_prompt()
    assert "{output}" in prompt and "{source}" in prompt


def test_prompt_excludes_generator_reasoning(sample_test_case_set):
    prompt = verify.build_verify_prompt(sample_test_case_set, "source doc")
    assert "reasoning" not in prompt.lower() or "did NOT generate" in prompt


def test_prompt_template_contains_only_output_and_source(sample_test_case_set):
    prompt = verify.build_verify_prompt(sample_test_case_set, "THE SOURCE")
    assert "THE SOURCE" in prompt
    assert sample_test_case_set.test_cases[0].tc_id in prompt


def test_verify_pass_on_clean_output(sample_test_case_set):
    client = MockVerifierClient([verdict_payload(passed=True)])
    verdict = verify.verify(sample_test_case_set, "src", client=client)
    assert verdict.passed


def test_verify_fail_on_problematic_output(sample_test_case_set):
    client = MockVerifierClient([verdict_payload(passed=False)])
    verdict = verify.verify(sample_test_case_set, "src", client=client)
    assert not verdict.passed


def test_verify_overwrites_model_field(sample_test_case_set):
    client = MockVerifierClient([verdict_payload()])
    verdict = verify.verify(sample_test_case_set, "src", client=client)
    assert verdict.model == "claude-mock"


def test_verify_unavailable_client_degrades(sample_test_case_set):
    class Unavailable:
        available = False
        model = None

    verdict = verify.verify(sample_test_case_set, "src", client=Unavailable())
    assert verdict.passed and verdict.confidence == 0.0
