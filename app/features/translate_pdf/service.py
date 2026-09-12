"""Orchestration: extract -> translate (chunked) -> generate."""

import logging
import time

from app.core.config import Settings, get_settings
from app.features.translate_pdf.pdf_extractor import extract_pages
from app.features.translate_pdf.pdf_generator import build_pdf
from app.features.translate_pdf.translator import Translator, build_translator

logger = logging.getLogger("pdf_editor")

_CHUNK_LIMIT = 1000  # generous chunk size for translation APIs


def get_translator(settings: Settings = get_settings()) -> Translator:
    return build_translator(settings)


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
    translated_pages: list[str] = []
    for page_text in pages:
        translated_chunks: list[str] = []
        for chunk in _chunk_text(page_text):
            if chunk.strip():
                translated = translator.translate(chunk, source, target)
                translated_chunks.append(translated)
                time.sleep(0.3)
            else:
                translated_chunks.append("")
        translated_pages.append("\n".join(translated_chunks))
    logger.info("translated %d page(s) %s -> %s", len(pages), source, target)
    return build_pdf(translated_pages)