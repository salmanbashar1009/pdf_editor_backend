"""Translation provider abstractions for PDF translation.

The module defines a `Translator` protocol and concrete implementations:
* :class:`MyMemoryTranslator` – free, key‑less MyMemory API with quota‑exhaustion handling.
* :class:`LibreTranslateTranslator` – free public LibreTranslate instances.
* :class:`GoogleTranslateTranslator` – free, keyless Google Translate web provider.
* :class:`FallbackTranslator` – composite translator that falls back to Google Translate if primary fails/hits quota.
"""

import logging
from typing import Protocol

import httpx
import time

from app.core.config import Settings
from app.core.exceptions import TranslationProviderError

logger = logging.getLogger("pdf_editor")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


class QuotaExhaustedError(TranslationProviderError):
    """Raised when translation quota has been exhausted (HTTP 429)."""
    status_code = 429


class Translator(Protocol):
    def translate(self, text: str, source: str, target: str) -> str: ...


class MyMemoryTranslator:
    """Real, keyless HTTPS translation provider (api.mymemory.translated.net)."""

    def __init__(self, url: str = "https://api.mymemory.translated.net/get", timeout: float = 30.0) -> None:
        self._url = url
        self._timeout = timeout
        self._quota_exhausted: bool = False
        self._cache: dict[tuple[str, str, str], str] = {}

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return text
        cache_key = (text, source, target)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self._quota_exhausted:
            raise QuotaExhaustedError("MyMemory free-tier quota has been exhausted for today")

        max_retries = 3
        backoff = 0.5
        for attempt in range(1, max_retries + 1):
            try:
                params = {"q": text, "langpair": f"{source}|{target}"}
                if getattr(self, "_api_key", None):
                    params["key"] = self._api_key
                
                headers = {"User-Agent": DEFAULT_USER_AGENT}
                try:
                    response = httpx.get(self._url, params=params, headers=headers, timeout=self._timeout)
                except httpx.ConnectError:
                    response = httpx.get(self._url, params=params, headers=headers, timeout=self._timeout, verify=False)

                if response.status_code == 429:
                    self._quota_exhausted = True
                    raise QuotaExhaustedError("MyMemory free-tier quota has been exhausted for today")
                
                response.raise_for_status()
                data = response.json()

                resp_details = str(data.get("responseDetails", "")).lower()
                translated = data.get("responseData", {}).get("translatedText") if isinstance(data.get("responseData"), dict) else None

                if "you used all available free translations" in resp_details or (translated and "MYMEMORY WARNING" in translated):
                    self._quota_exhausted = True
                    raise QuotaExhaustedError("MyMemory free-tier quota has been exhausted for today")

                if not translated:
                    raise TranslationProviderError("Translation provider returned no text")

                self._cache[cache_key] = translated
                time.sleep(0.2)
                return translated
            except QuotaExhaustedError:
                raise
            except httpx.HTTPStatusError as http_exc:
                if http_exc.response.status_code == 429:
                    self._quota_exhausted = True
                    raise QuotaExhaustedError("MyMemory free-tier quota has been exhausted for today") from http_exc
                if attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise TranslationProviderError("Translation provider failure; try again later") from http_exc
            except Exception as exc:
                if attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise TranslationProviderError("Translation provider failure; try later") from exc
        raise TranslationProviderError("Translation provider failure after retries")


class LibreTranslateTranslator:
    """Wrapper for LibreTranslate (https://libretranslate.com)."""

    def __init__(self, url: str = "https://libretranslate.de", timeout: float = 30.0) -> None:
        self._url = url.rstrip('/')
        self._timeout = timeout
        self._quota_exhausted: bool = False
        self._cache: dict[tuple[str, str, str], str] = {}

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return text
        cache_key = (text, source, target)
        if cache_key in self._cache:
            return self._cache[cache_key]

        payload = {
            "q": text,
            "source": source,
            "target": target,
            "format": "text",
        }
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        try:
            response = httpx.post(
                f"{self._url}/translate",
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
        except httpx.ConnectError:
            response = httpx.post(
                f"{self._url}/translate",
                json=payload,
                headers=headers,
                timeout=self._timeout,
                verify=False,
            )
        response.raise_for_status()
        data = response.json()
        translated = data.get("translatedText")
        if not translated:
            raise TranslationProviderError("LibreTranslate returned empty result")
        self._cache[cache_key] = translated
        time.sleep(0.2)
        return translated


class GoogleTranslateTranslator:
    """Free key-less Google Translate provider via translate.googleapis.com endpoint."""

    def __init__(self, url: str = "https://translate.googleapis.com/translate_a/single", timeout: float = 30.0) -> None:
        self._url = url
        self._timeout = timeout
        self._quota_exhausted: bool = False
        self._cache: dict[tuple[str, str, str], str] = {}

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return text
        cache_key = (text, source, target)
        if cache_key in self._cache:
            return self._cache[cache_key]

        max_retries = 3
        backoff = 0.5
        for attempt in range(1, max_retries + 1):
            try:
                params = {
                    "client": "gtx",
                    "sl": source,
                    "tl": target,
                    "dt": "t",
                    "q": text,
                }
                headers = {
                    "User-Agent": DEFAULT_USER_AGENT,
                    "Accept": "*/*",
                }
                try:
                    response = httpx.get(self._url, params=params, headers=headers, timeout=self._timeout)
                except httpx.ConnectError:
                    response = httpx.get(self._url, params=params, headers=headers, timeout=self._timeout, verify=False)

                response.raise_for_status()
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    parts = [item[0] for item in data[0] if item and isinstance(item, list) and len(item) > 0 and item[0]]
                    translated = "".join(parts)
                    if translated:
                        self._cache[cache_key] = translated
                        time.sleep(0.1)
                        return translated
                raise TranslationProviderError("Google Translate returned empty result")
            except Exception as exc:
                if attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise TranslationProviderError("Google Translate provider failure; try later") from exc
        raise TranslationProviderError("Google Translate provider failure after retries")


class FallbackTranslator:
    """Composite translator that attempts primary provider, and falls back to Google Translate on failure."""

    def __init__(self, primary: Translator, fallback: Translator | None = None) -> None:
        self._primary = primary
        self._fallback = fallback or GoogleTranslateTranslator()

    def translate(self, text: str, source: str, target: str) -> str:
        try:
            return self._primary.translate(text, source, target)
        except (QuotaExhaustedError, TranslationProviderError) as err:
            logger.warning("Primary translator failed (%s). Falling back to Google Translate.", err)
            return self._fallback.translate(text, source, target)


def build_translator(settings: Settings) -> Translator:
    """Construct a translator based on configured URL with automatic Google Translate fallback."""
    url = settings.translation_api_url
    if "google" in url.lower():
        primary: Translator = GoogleTranslateTranslator(url, settings.request_timeout)
    elif "libretranslate" in url.lower():
        primary = LibreTranslateTranslator(url, settings.request_timeout)
    else:
        primary = MyMemoryTranslator(url, settings.request_timeout)

    if getattr(settings, "translation_api_key", None):
        setattr(primary, "_api_key", settings.translation_api_key)

    # Wrap in FallbackTranslator to seamlessly fall back to Google Translate if primary hits quota/errors
    if isinstance(primary, GoogleTranslateTranslator):
        return primary
    return FallbackTranslator(primary=primary, fallback=GoogleTranslateTranslator(timeout=settings.request_timeout))