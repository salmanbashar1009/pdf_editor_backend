"""Language contract for the translation API."""

from fastapi import HTTPException

SUPPORTED_LANGUAGES = frozenset(
    {"en", "bn", "es", "fr", "de", "hi", "ar", "pt", "ru", "ja", "ko", "zh", "it", "nl", "tr", "ur"}
)


def parse_language(value: str | None, field: str) -> str:
    if value is None or not value.strip():
        raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    code = value.strip().lower()
    if code not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail=f"Unsupported language code: {code}")
    return code