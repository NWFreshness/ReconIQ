"""Local raw-response cache for LLM completions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from core.settings import PROJECT_ROOT


def default_cache_dir(config: dict[str, Any] | None = None) -> Path:
    cfg = (config or {}).get("llm_cache", {})
    raw_path = cfg.get("path") or ".reconiq-cache/llm"
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def is_cache_enabled(config: dict[str, Any] | None = None) -> bool:
    return bool((config or {}).get("llm_cache", {}).get("enabled", True))


def make_cache_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_cached_response(cache_key: str, cache_dir: Path | None = None) -> str | None:
    try:
        path = (cache_dir or default_cache_dir()) / f"{cache_key}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get("raw_response")
        return raw if isinstance(raw, str) else None
    except Exception:
        return None


def write_cached_response(cache_key: str, raw: str, cache_dir: Path | None = None) -> None:
    try:
        directory = cache_dir or default_cache_dir()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{cache_key}.json"
        path.write_text(json.dumps({"raw_response": raw}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        return


def build_llm_cache_payload(
    *,
    module: str,
    provider: str,
    model: str | None,
    system: str | None,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    return {
        "module": module,
        "provider": provider,
        "model": model,
        "system": system,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
