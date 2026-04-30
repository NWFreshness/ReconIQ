"""Framework-neutral configuration loading for ReconIQ."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"

load_dotenv(PROJECT_ROOT / ".env")


def resolve_env_values(value: Any) -> Any:
    """Recursively resolve ${ENV_VAR} strings inside config data."""
    if isinstance(value, dict):
        return {key: resolve_env_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_env_values(item) for item in value]
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.getenv(value[2:-1], "")
    return value


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load ReconIQ YAML config from an explicit path or the project default."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    with config_path.expanduser().open(encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}
    return resolve_env_values(raw)
