"""Translation provider, isolated behind a protocol for replaceability/tests."""

from typing import Protocol

import httpx

from app.core.config import Settings
from app.core.exceptions import TranslationProviderError


class Translator(Protocol):
    def translate(self, text: str, source: str, target: str) -> str: ...


class MyMemoryTranslator:
    """Real, keyless HTTPS translation provider (api.mymemory.translated.net)."""

    def __init__(self, url: str, timeout: float = 30.0) -> None:
        self._url = url
        self._timeout = timeout

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return text
        try:
            response = httpx.get(
                self._url,
                params={"q": text, "langpair": f"{source}|{target}"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            translated = response.json()["responseData"]["translatedText"]
            if not translated:
                raise ValueError("empty translation")
            return translated
        except Exception as exc:
            raise TranslationProviderError(
                "Translation provider failure; try again later"
            ) from exc


def build_translator(settings: Settings) -> Translator:
    return MyMemoryTranslator(settings.translation_api_url, settings.request_timeout)