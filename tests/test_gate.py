import copy

from apps.api.evals.metrics import gate
from apps.api.models import TestCaseSet


def test_gate_passes_on_valid(sample_test_case_set):
    assert gate(sample_test_case_set).passed


def test_gate_passes_on_empty():
    assert gate(TestCaseSet()).passed


def test_gate_fails_on_bad_gherkin(sample_test_case_set):
    bad = copy.deepcopy(sample_test_case_set)
    bad.test_cases[0].gherkin.steps = []
    bad.test_cases[0].gherkin.title = ""
    result = gate(bad)
    assert not result.passed and not result.gherkin_pass


def test_gate_fails_on_duplicates(sample_test_case_set):
    dup = copy.deepcopy(sample_test_case_set)
    clone = copy.deepcopy(dup.test_cases[0])
    clone.tc_id = "TC-DUP"
    dup.test_cases.append(clone)
    result = gate(dup)
    assert not result.passed and result.dup_count >= 1


def test_gate_captures_both_failure_types(sample_test_case_set):
    bad = copy.deepcopy(sample_test_case_set)
    bad.test_cases[0].gherkin.steps = []
    bad.test_cases[0].gherkin.title = ""
    result = gate(bad)
    assert result.errors


def test_gate_captures_gherkin_failure(sample_test_case_set):
    bad = copy.deepcopy(sample_test_case_set)
    bad.test_cases[1].gherkin.title = ""
    bad.test_cases[1].gherkin.steps = []
    result = gate(bad)
    assert any(bad.test_cases[1].tc_id in e for e in result.errors)


def test_gate_combined_failures(sample_test_case_set):
    bad = copy.deepcopy(sample_test_case_set)
    bad.test_cases[0].gherkin.steps = []
    bad.test_cases[0].gherkin.title = ""
    clone = copy.deepcopy(bad.test_cases[1])
    clone.tc_id = "TC-DUP"
    bad.test_cases.append(clone)
    result = gate(bad)
    assert not result.passed and not result.gherkin_pass and result.dup_count >= 1
