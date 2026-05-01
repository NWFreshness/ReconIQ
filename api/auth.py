"""API key authentication for ReconIQ FastAPI backend."""
from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_ENV = "RECONIQ_API_KEY"
_DEFAULT_KEY = "reconiq-dev-key-change-in-production"

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key() -> str:
    return os.environ.get(API_KEY_ENV, _DEFAULT_KEY)


async def verify_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> str:
    expected = get_api_key()
    if api_key == expected:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )
