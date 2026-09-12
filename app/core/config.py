"""Centralized, environment-driven configuration (no secrets committed)."""

import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    environment: str = "development"
    log_level: str = "INFO"
    max_upload_size: int = 10 * 1024 * 1024
    translation_api_url: str = "https://api.mymemory.translated.net/get"
    translation_api_key: str | None = None
    request_timeout: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("ENVIRONMENT", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        max_upload_size=int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024))),
        translation_api_url=os.getenv(
            "TRANSLATION_API_URL", "https://api.mymemory.translated.net/get"
        ),
        translation_api_key=os.getenv("TRANSLATION_API_KEY") or None,
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "30")),
    )