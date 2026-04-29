"""LLM Router — unified interface for all providers via litellm."""
from __future__ import annotations

import os
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv()


def _resolve_env(value: str) -> str:
    """Resolve ${ENV_VAR} references in config values."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.getenv(env_var, "")
    return value


def _load_config() -> dict:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml")
    if not os.path.exists(config_path):
        # Try the project directory
        config_path = os.path.expanduser("~/Documents/ai-automation-agency/ReconIQ/config.yaml")
    with open(config_path) as f:
        raw = yaml.safe_load(f)

    def resolve(d):
        if isinstance(d, dict):
            return {k: resolve(v) for k, v in d.items()}
        if isinstance(d, list):
            return [resolve(v) for v in d]
        return _resolve_env(d)

    return resolve(raw)


# Cache config on module load
config = _load_config()


def get_config() -> dict:
    """Return the loaded config (useful for UI and testing)."""
    return config


def _get_module_provider_model(module_name: str) -> tuple[str, Optional[str]]:
    """Return (provider, model) for a given module."""
    modules = config.get("modules", {})
    mod = modules.get(module_name, {})
    provider = mod.get("provider", config.get("defaults", {}).get("provider", "deepseek"))
    model = mod.get("model")
    return provider, model


def _build_model_string(provider: str, model: Optional[str]) -> str:
    """Build the litellm-compatible model string."""
    if model:
        return f"{provider}/{model}"
    # Use provider's default model from config
    default_model = config.get("providers", {}).get(provider, {}).get("default_model")
    if default_model:
        return f"{provider}/{default_model}"
    return f"{provider}/default"


def complete(
    prompt: str,
    module: str,
    system: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> str:
    """
    Send a completion request to the appropriate LLM for a research module.

    Args:
        prompt: The user prompt.
        module: Module name matching config keys (e.g. 'company_profile', 'competitor').
        system: Optional system prompt override.
        max_tokens: Max response tokens.
        temperature: Sampling temperature.

    Returns:
        The raw text response from the LLM.

    Raises:
        RuntimeError: If all attempts fail.
    """
    from litellm import completion

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    provider, model = _get_module_provider_model(module)

    # Build the list of providers to try (original, then fallback)
    providers_to_try = [provider]
    if provider != "deepseek":
        providers_to_try.append("deepseek")

    last_error = None
    for current_provider in providers_to_try:
        current_model = model if current_provider == provider else None
        model_string = _build_model_string(current_provider, current_model)

        kwargs: dict = {
            "model": model_string,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Ollama needs api_base
        if current_provider == "ollama":
            endpoint = config.get("providers", {}).get("ollama", {}).get("endpoint", "http://localhost:11434")
            kwargs["api_base"] = endpoint

        try:
            response = completion(**kwargs)
            return response.choices[0].message.content
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"LLM call failed after fallback: {last_error}")


def check_ollama() -> bool:
    """Check if Ollama is reachable at its configured endpoint."""
    try:
        import requests as http_requests
        endpoint = config.get("providers", {}).get("ollama", {}).get("endpoint", "http://localhost:11434")
        r = http_requests.get(f"{endpoint}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False