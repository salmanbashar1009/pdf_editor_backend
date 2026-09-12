"""Orchestration: extract -> translate (chunked) -> generate."""

import logging
from collections.abc import Callable

from app.core.config import Settings, get_settings
from app.features.translate_pdf.pdf_extractor import extract_pages
from app.features.translate_pdf.pdf_generator import build_pdf
from app.features.translate_pdf.translator import MyMemoryTranslator, Translator

logger = logging.getLogger("pdf_editor")

_CHUNK_LIMIT = 450  # MyMemory GET limit is ~500 bytes per request


def get_translator(settings: Settings = get_settings()) -> Translator:
    return MyMemoryTranslator(settings.translation_url if False else settings.translation_api_url,
                              settings.request_timeout)


def _chunk_text(text: str, limit: int = _CHUNK_LIMIT) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        piece = line if not current else f"\n{line}"
        if len(current) + len(piece) <= limit:
            current += piece
        else:
            if current:
                chunks.append(current)
            while len(line) > limit:
                chunks.append(line[:limit])
                line = line[limit:]
            current = line
    if current:
        chunks.append(current)
    return chunks


def translate_pdf(pdf_bytes: bytes, source: str, target: str, translator: Translator) -> bytes:
    pages = extract_pages(pdf_bytes)
    translated_pages = [
        "\n".join(
            translator.translate(chunk, source, target) if chunk.strip() else ""
            for chunk in _chunk_text(page_text)
        )
        for page_text in pages
    ]
    logger.info("translated %d page(s) %s->%s", len(pages), source, target)
    return build_pdf(translated_pages)