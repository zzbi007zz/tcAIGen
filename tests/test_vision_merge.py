import pytest

from apps.api.models import (
    AcceptanceCriterion, DocumentMeta, Feature, GapType, RequirementsDocument,
    Screen, UIElement, UIInventory,
)
from apps.api.pipeline import merge, vision
from apps.api.pipeline.gemini_client import GeminiClient


def make_reqs():
    return RequirementsDocument(
        meta=DocumentMeta(title="D", source_type="paste"),
        features=[
            Feature(id="F1", name="User Login", description="login with email password",
                    source_location="S1",
                    acceptance_criteria=[AcceptanceCriterion(
                        id="A1", text="login works", source_location="S1.1")]),
            Feature(id="F2", name="Reporting Dashboard", description="charts and export",
                    source_location="S2",
                    acceptance_criteria=[AcceptanceCriterion(
                        id="A2", text="export works", source_location="S2.1")]),
        ])


def make_inventory():
    return UIInventory(screens=[
        Screen(screen_id="S1", screen_name="Login Screen",
               elements=[UIElement(element_id="e1", element_type="input", label="email"),
                         UIElement(element_id="e2", element_type="button", label="login")]),
        Screen(screen_id="S2", screen_name="Admin Settings",
               elements=[UIElement(element_id="e3", element_type="label", label="admin panel")]),
    ])


class TestMapping:
    def test_feature_screen_match(self):
        mappings = merge.map_features_to_screens(make_reqs(), make_inventory())
        assert any(m.feature_id == "F1" and m.screen_id == "S1" for m in mappings)

    def test_perfect_match_no_gaps(self):
        reqs = make_reqs()
        reqs.features = reqs.features[:1]
        inv = make_inventory()
        inv.screens = inv.screens[:1]
        result = merge.merge_and_analyze(reqs, inv)
        assert result.gaps == []

    def test_merge_result_structure(self):
        result = merge.merge_and_analyze(make_reqs(), make_inventory())
        assert result.mappings and result.gaps
        assert "F2" in result.unmapped_features
        assert "S2" in result.unmapped_screens


class TestGapDetection:
    def test_requirement_without_design_gap(self):
        gaps = merge.merge_and_analyze(make_reqs(), make_inventory()).gaps
        assert any(g.gap_type == GapType.requirement_without_design and g.subject_id == "F2"
                   for g in gaps)

    def test_design_without_requirement_gap(self):
        gaps = merge.merge_and_analyze(make_reqs(), make_inventory()).gaps
        assert any(g.gap_type == GapType.design_without_requirement and g.subject_id == "S2"
                   for g in gaps)

    def test_validation_mismatch(self):
        reqs = make_reqs()
        reqs.features = reqs.features[:1]
        from apps.api.models import InputValidation
        reqs.features[0].acceptance_criteria[0].validations = [
            InputValidation(field="phone_number", constraint="10 digits")]
        inv = make_inventory()
        inv.screens = inv.screens[:1]
        gaps = merge.detect_gaps(merge.map_features_to_screens(reqs, inv), reqs, inv)
        assert any(g.gap_type == GapType.validation_mismatch for g in gaps)

    def test_empty_inventory(self):
        result = merge.merge_and_analyze(make_reqs(), UIInventory())
        assert result.mappings == []
        assert len(result.unmapped_features) == 2

    def test_empty_requirements(self):
        result = merge.merge_and_analyze(
            RequirementsDocument(meta=DocumentMeta(title="E", source_type="paste")),
            make_inventory())
        assert result.mappings == []
        assert len(result.unmapped_screens) == 2


class TestVision:
    def test_mime_type_detection(self):
        assert vision.mime_type_from_file("a.png") == "image/png"
        assert vision.mime_type_from_file("a.jpg") == "image/jpeg"
        with pytest.raises(ValueError):
            vision.mime_type_from_file("a.gif")

    def test_no_api_key(self, monkeypatch, fixtures_dir):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        client = GeminiClient(api_key=None)
        result = vision.run_vision_pipeline(
            [fixtures_dir / "sample_screenshot.png"], client=client)
        assert result.screens == []
