from apps.api.models import Category, Gherkin, ScenarioType, TestCase, TestCaseSet, TestStep
from apps.api.pipeline.export import gherkin_writer


def tc(tc_id, fid="F1", outline=False):
    return TestCase(
        tc_id=tc_id, feature_id=fid, title=f"Title {tc_id}", category=Category.positive,
        priority="high", grounding_source="AC1",
        gherkin=Gherkin(
            scenario_type=ScenarioType.scenario_outline if outline else ScenarioType.scenario,
            title=f"Scenario {tc_id}", tags=["@positive"],
            steps=[TestStep(keyword="Given", text="precondition"),
                   TestStep(keyword="When", text="action"),
                   TestStep(keyword="Then", text="outcome")],
            examples_table=[{"x": "1"}, {"x": "2"}] if outline else None,
        ))


def test_formats_scenario():
    text = gherkin_writer.format_gherkin(tc("T1").gherkin)
    assert "Scenario: Scenario T1" in text
    assert "Given precondition" in text
    assert "@positive" in text


def test_formats_scenario_outline_with_examples():
    text = gherkin_writer.format_gherkin(tc("T2", outline=True).gherkin)
    assert "Scenario Outline: Scenario T2" in text
    assert "Examples:" in text
    assert "| x |" in text


def test_write_file_creates_files(tmp_path):
    tcs = TestCaseSet(test_cases=[tc("A"), tc("B"), tc("C", fid="F2")])
    written = gherkin_writer.write_feature_file(tcs, tmp_path, feature_names={"F1": "Login", "F2": "Reset"})
    assert len(written) == 2
    assert (tmp_path / "f1.feature").exists()
    assert "Feature: Login" in (tmp_path / "f1.feature").read_text()


def test_empty_test_case_set(tmp_path):
    assert gherkin_writer.write_feature_file(TestCaseSet(), tmp_path) == []


def test_feature_file_content_parses(tmp_path):
    from apps.api.pipeline.generate import validate_gherkin
    tcs = TestCaseSet(test_cases=[tc("A")])
    gherkin_writer.write_feature_file(tcs, tmp_path)
    assert validate_gherkin(tcs) == []
