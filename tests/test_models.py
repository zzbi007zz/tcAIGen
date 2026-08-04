import pytest
from pydantic import ValidationError

from apps.api.models import (
    AcceptanceCriterion, DocumentMeta, ExtractionConfidence, Feature,
    FeatureScreenMapping, Gap, GapType, Gherkin, Grounding, InputValidation,
    MergeResult, RequirementsDocument, Screen, SourceType, TestCase,
    TestCaseSet, TestStep, UIElement, UIInventory, VerifierVerdict,
    FailedCriterion, GateResult, LoopBudget, VisionConfidence, Category,
    ScenarioType,
)


def roundtrip(model):
    return type(model).model_validate_json(model.model_dump_json())


def make_document():
    return RequirementsDocument(
        meta=DocumentMeta(title="Doc", source_type=SourceType.paste),
        features=[Feature(
            id="F1", name="Login", description="User login", source_location="S1",
            acceptance_criteria=[AcceptanceCriterion(
                id="AC1", text="Valid login works", grounding=Grounding.explicit,
                source_location="S1.1",
                validations=[InputValidation(field="email", constraint="valid format")],
            )],
        )],
        confidence=ExtractionConfidence(explicit_criteria_count=1, inferred_criteria_count=0),
    )


def make_test_case(tc_id="TC-1"):
    return TestCase(
        tc_id=tc_id, feature_id="F1", title="Login ok", category=Category.positive,
        priority="high", grounding_source="AC1 text",
        gherkin=Gherkin(title="Login", steps=[TestStep(keyword="Given", text="a user")]),
    )


class TestRequirementsModels:
    def test_document_meta_roundtrip(self):
        assert roundtrip(DocumentMeta(title="T", source_type="word")).title == "T"

    def test_source_type_values(self):
        assert {s.value for s in SourceType} == {"word", "pdf", "paste"}

    def test_acceptance_criterion_grounding_default(self):
        ac = AcceptanceCriterion(id="A", text="t", source_location="s")
        assert ac.grounding == Grounding.explicit

    def test_input_validation_defaults(self):
        v = InputValidation(field="email", constraint="format")
        assert v.grounding == Grounding.explicit

    def test_feature_roundtrip(self):
        f = make_document().features[0]
        assert roundtrip(f) == f

    def test_requirements_document_roundtrip(self):
        assert roundtrip(make_document()) == make_document()

    def test_confidence_counts_sum(self):
        c = ExtractionConfidence(explicit_criteria_count=3, inferred_criteria_count=2)
        assert c.total_criteria == 5

    def test_confidence_negative_rejected(self):
        with pytest.raises(ValidationError):
            ExtractionConfidence(explicit_criteria_count=-1)


class TestUIInventoryModels:
    def test_ui_element_roundtrip(self):
        e = UIElement(element_id="e1", element_type="button", label="Save")
        assert roundtrip(e) == e

    def test_screen_confidence_default(self):
        s = Screen(screen_id="s1", screen_name="Home")
        assert s.vision_confidence == VisionConfidence.medium

    def test_screen_confidence_values(self):
        assert {v.value for v in VisionConfidence} == {"high", "medium", "low"}

    def test_inventory_roundtrip(self):
        inv = UIInventory(screens=[Screen(screen_id="s1", screen_name="Home",
                                          elements=[UIElement(element_id="e", element_type="input")])])
        assert roundtrip(inv) == inv


class TestMergeGapModels:
    def test_gap_type_enum(self):
        assert {g.value for g in GapType} == {
            "requirement_without_design", "design_without_requirement", "validation_mismatch"}

    def test_invalid_gap_type_rejected(self):
        with pytest.raises(ValidationError):
            Gap(gap_type="nonsense", subject_id="x", note="n")

    def test_mapping_roundtrip(self):
        m = FeatureScreenMapping(feature_id="F1", screen_id="S1", similarity_score=0.5)
        assert roundtrip(m) == m

    def test_merge_result_roundtrip(self):
        r = MergeResult(
            mappings=[FeatureScreenMapping(feature_id="F1", screen_id="S1")],
            gaps=[Gap(gap_type=GapType.design_without_requirement, subject_id="S2", note="n")],
            unmapped_features=["F2"], unmapped_screens=["S2"])
        assert roundtrip(r) == r


class TestTestCaseModels:
    def test_grounding_source_mandatory(self):
        with pytest.raises(ValidationError):
            TestCase(tc_id="T", feature_id="F", title="t",
                     gherkin=Gherkin(title="g"))

    def test_test_case_roundtrip(self):
        assert roundtrip(make_test_case()) == make_test_case()

    def test_scenario_outline_with_examples(self):
        tc = make_test_case()
        tc.gherkin.scenario_type = ScenarioType.scenario_outline
        tc.gherkin.examples_table = [{"a": "1"}]
        assert roundtrip(tc).gherkin.examples_table == [{"a": "1"}]

    def test_test_case_set_roundtrip(self):
        s = TestCaseSet(source_doc_title="D", test_cases=[make_test_case("A"), make_test_case("B")])
        assert roundtrip(s) == s

    def test_category_values(self):
        assert {c.value for c in Category} == {"positive", "negative", "edge", "boundary"}


class TestVerdictModels:
    def test_failed_criterion(self):
        f = FailedCriterion(criterion="c", reason="r", tc_id="T1")
        assert roundtrip(f) == f

    def test_verifier_verdict_defaults(self):
        v = VerifierVerdict(passed=True)
        assert v.confidence == 1.0 and v.failed_criteria == []

    def test_gate_result_defaults(self):
        g = GateResult(passed=True)
        assert g.gherkin_pass and g.dup_count == 0

    def test_loop_budget_defaults(self):
        b = LoopBudget()
        assert b.max_iterations == 3 and b.no_progress_stop
