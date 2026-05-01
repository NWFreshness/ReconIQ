from __future__ import annotations

from types import SimpleNamespace

import pytest

from llm import router


BASE_CONFIG = {
    "providers": {
        "openai": {"default_model": "gpt-4o-mini"},
        "deepseek": {"default_model": "deepseek-chat"},
        "anthropic": {"default_model": "claude-3-5-sonnet-latest"},
        "groq": {"default_model": "llama-3.3-70b-versatile"},
        "ollama": {"endpoint": "http://localhost:11434", "default_model": "llama3"},
    },
    "defaults": {"provider": "deepseek", "model": None},
    "modules": {
        "company_profile": {"provider": "deepseek", "model": None},
        "competitor": {"provider": "anthropic", "model": None},
        "social_content": {"provider": "openai", "model": None},
        "custom": {"provider": "groq", "model": "llama-special"},
    },
}


def _response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )




@pytest.fixture(autouse=True)
def disable_llm_cache(monkeypatch):
    monkeypatch.setattr("llm.router.is_cache_enabled", lambda _cfg=None: False)

def test_get_module_provider_model_uses_module_config():
    provider, model = router.get_module_provider_model("competitor", BASE_CONFIG)

    assert provider == "anthropic"
    assert model is None


def test_get_module_provider_model_falls_back_to_defaults_for_unknown_module():
    provider, model = router.get_module_provider_model("unknown", BASE_CONFIG)

    assert provider == "deepseek"
    assert model is None


def test_resolve_model_uses_provider_default_when_model_is_none():
    assert router.resolve_model("deepseek", None, BASE_CONFIG) == "deepseek/deepseek-chat"
    assert router.resolve_model("anthropic", None, BASE_CONFIG) == "anthropic/claude-3-5-sonnet-latest"


def test_resolve_model_uses_explicit_model():
    assert router.resolve_model("groq", "llama-special", BASE_CONFIG) == "groq/llama-special"


def test_build_completion_kwargs_sets_ollama_api_base():
    messages = [{"role": "user", "content": "hello"}]

    kwargs = router.build_completion_kwargs("ollama", None, messages, BASE_CONFIG)

    assert kwargs["model"] == "ollama/llama3"
    assert kwargs["api_base"] == "http://localhost:11434"
    assert kwargs["messages"] == messages


def test_complete_allows_provider_and_model_overrides(monkeypatch):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        return _response("ok")

    monkeypatch.setattr(router, "completion", fake_completion)
    monkeypatch.setattr(router, "config", BASE_CONFIG)

    result = router.complete(
        "prompt",
        module="competitor",
        provider_override="openai",
        model_override="gpt-4o-mini",
    )

    assert result == "ok"
    assert calls[0]["model"] == "openai/gpt-4o-mini"


def test_complete_falls_back_to_deepseek_on_first_provider_failure(monkeypatch):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("provider down")
        return _response("fallback ok")

    monkeypatch.setattr(router, "completion", fake_completion)
    monkeypatch.setattr(router, "config", BASE_CONFIG)

    result = router.complete("prompt", module="competitor")

    assert result == "fallback ok"
    assert calls[0]["model"] == "anthropic/claude-3-5-sonnet-latest"
    assert calls[1]["model"] == "deepseek/deepseek-chat"


def test_complete_never_uses_provider_default_literal(monkeypatch):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        return _response("ok")

    monkeypatch.setattr(router, "completion", fake_completion)
    monkeypatch.setattr(router, "config", BASE_CONFIG)

    router.complete("prompt", module="company_profile")

    assert calls[0]["model"] != "deepseek/default"
