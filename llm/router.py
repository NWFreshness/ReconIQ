"""LLM Router — unified interface for all providers via LiteLLM."""
from __future__ import annotations

from typing import Any

import requests as http_requests
from litellm import completion

from core.settings import load_config

config = load_config()


def get_config() -> dict[str, Any]:
    """Return the loaded config for UI display and tests."""
    return config


def get_module_provider_model(module_name: str, loaded_config: dict[str, Any] | None = None) -> tuple[str, str | None]:
    """Return the configured provider and model for a module."""
    cfg = loaded_config or config
    defaults = cfg.get("defaults", {})
    module_config = cfg.get("modules", {}).get(module_name, {})
    provider = module_config.get("provider") or defaults.get("provider") or "deepseek"
    model = module_config.get("model", defaults.get("model"))
    return provider, model


def resolve_model(provider: str, model: str | None, loaded_config: dict[str, Any] | None = None) -> str:
    """Build a LiteLLM-compatible model string without using provider/default sentinels."""
    cfg = loaded_config or config
    resolved_model = model or cfg.get("providers", {}).get(provider, {}).get("default_model")
    if not resolved_model:
        raise ValueError(f"No model configured for provider '{provider}'")
    return f"{provider}/{resolved_model}"


def build_completion_kwargs(
    provider: str,
    model: str | None,
    messages: list[dict[str, str]],
    loaded_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build LiteLLM completion kwargs for a provider/model pair."""
    cfg = loaded_config or config
    kwargs: dict[str, Any] = {
        "model": resolve_model(provider, model, cfg),
        "messages": messages,
    }
    if provider == "ollama":
        kwargs["api_base"] = cfg.get("providers", {}).get("ollama", {}).get("endpoint", "http://localhost:11434")
    return kwargs


def _providers_to_try(provider: str) -> list[str]:
    providers = [provider]
    if provider != "deepseek":
        providers.append("deepseek")
    return providers


def complete(
    prompt: str,
    module: str,
    system: str | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    provider_override: str | None = None,
    model_override: str | None = None,
) -> str:
    """Send a completion request to the configured LLM for a research module."""
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    configured_provider, configured_model = get_module_provider_model(module, config)
    provider = provider_override or configured_provider
    model = model_override if model_override is not None else configured_model

    last_error: Exception | None = None
    for current_provider in _providers_to_try(provider):
        current_model = model if current_provider == provider else None
        kwargs = build_completion_kwargs(current_provider, current_model, messages, config)
        kwargs["max_tokens"] = max_tokens
        kwargs["temperature"] = temperature
        try:
            response = completion(**kwargs)
            return response.choices[0].message.content
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"LLM call failed after fallback: {last_error}")


def check_ollama() -> bool:
    """Check if Ollama is reachable at its configured endpoint."""
    try:
        endpoint = config.get("providers", {}).get("ollama", {}).get("endpoint", "http://localhost:11434")
        response = http_requests.get(f"{endpoint}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
