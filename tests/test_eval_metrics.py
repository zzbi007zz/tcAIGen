import copy

from apps.api.evals import calibration, metrics
from apps.api.models import RequirementsDocument, TestCaseSet


class TestACCoverage:
    def test_full_coverage(self, sample_test_case_set, sample_requirements_doc):
        score, uncovered = metrics.compute_ac_coverage(sample_test_case_set, sample_requirements_doc)
        assert score > 0.8

    def test_partial_coverage(self, sample_test_case_set, sample_requirements_doc):
        reduced = TestCaseSet(test_cases=sample_test_case_set.test_cases[:1])
        score, uncovered = metrics.compute_ac_coverage(reduced, sample_requirements_doc)
        assert score < 1.0 and uncovered


class TestCategoryBalance:
    def test_good_balance(self, sample_test_case_set):
        balance = metrics.compute_category_balance(sample_test_case_set)
        assert balance["negative"] >= 0.3

    def test_low_negative_ratio(self, sample_test_case_set):
        positives = TestCaseSet(test_cases=[
            tc for tc in sample_test_case_set.test_cases if tc.category.value == "positive"])
        balance = metrics.compute_category_balance(positives)
        assert balance["negative"] == 0.0


class TestFaithfulness:
    def test_all_grounded(self, sample_test_case_set):
        score = metrics.compute_faithfulness(sample_test_case_set)
        assert score == 1.0

    def test_empty_grounding_source(self, sample_test_case_set):
        bad = copy.deepcopy(sample_test_case_set)
        for tc in bad.test_cases:
            tc.grounding_source = ""
        assert metrics.compute_faithfulness(bad) == 0.0


class TestGherkinValidity:
    def test_all_gherkin_valid(self, sample_test_case_set):
        assert metrics.validate_gherkin_syntax(sample_test_case_set) == []

    def test_invalid_gherkin_reported(self, sample_test_case_set):
        bad = copy.deepcopy(sample_test_case_set)
        bad.test_cases[0].gherkin.steps = []
        bad.test_cases[0].gherkin.title = ""
        failures = metrics.validate_gherkin_syntax(bad)
        assert bad.test_cases[0].tc_id in failures


class TestDuplication:
    def test_no_duplicates(self, sample_test_case_set):
        assert metrics.detect_duplicates(sample_test_case_set) == []

    def test_similar_cases(self, sample_test_case_set):
        dup = copy.deepcopy(sample_test_case_set)
        clone = copy.deepcopy(dup.test_cases[0])
        clone.tc_id = "TC-CLONE"
        dup.test_cases.append(clone)
        pairs = metrics.detect_duplicates(dup)
        assert any("TC-CLONE" in pair for pair in pairs)


class TestInferredRatio:
    def test_mixed_grounding(self, sample_test_case_set):
        ratio = metrics.compute_inferred_ratio(sample_test_case_set)
        assert 0.0 < ratio < 1.0


class TestFullReportAndGate:
    def test_full_report(self, sample_test_case_set, sample_requirements_doc, sample_ba_text):
        report = metrics.evaluate_all(sample_test_case_set, sample_requirements_doc, sample_ba_text)
        assert 0 <= report.overall_score <= 100
        assert set(report.breakdown) >= {"ac_coverage", "category_balance", "faithfulness",
                                         "inferred_ratio", "gherkin_validity"}

    def test_gate_passes_on_valid(self, sample_test_case_set):
        result = metrics.gate(sample_test_case_set)
        assert result.passed and result.gherkin_pass and result.dup_count == 0


class TestCalibration:
    def test_run_calibration(self):
        result = calibration.run_calibration()
        assert result["n"] == 7
        assert -1.0 <= result["kappa"] <= 1.0

    def test_kappa_perfect_agreement(self):
        assert calibration.compute_kappa([True, False, True], [True, False, True]) == 1.0
