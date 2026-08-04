import pytest

from apps.api.pipeline import model_router
from apps.api.pipeline.gemini_client import GeminiClient
from apps.api.pipeline.model_router import OpenRouterClient


def test_generate_and_verify_different_models():
    assert model_router.ROLES["generate"]["provider"] == "gemini"
    assert model_router.ROLES["verify"]["provider"] == "openrouter"


def test_verify_returns_openrouter_client():
    assert isinstance(model_router.get_client("verify"), OpenRouterClient)


def test_generate_returns_gemini_client():
    assert isinstance(model_router.get_client("generate"), GeminiClient)


def test_judge_role_different_from_verify():
    assert model_router.ROLES["judge"]["model"] != model_router.ROLES["verify"]["model"]


def test_unknown_role_raises():
    with pytest.raises(ValueError):
        model_router.get_client("nope")


def test_get_fallback_for_unknown_role_raises():
    with pytest.raises(ValueError):
        model_router.get_fallback_models("nope")


def test_get_fallback_models_for_judge():
    assert model_router.get_fallback_models("judge")


def test_openrouter_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert not OpenRouterClient(model="x", api_key=None).available
