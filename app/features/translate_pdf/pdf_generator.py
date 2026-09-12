

from pathlib import Path

import pymupdf

FONT_DIR = Path(__file__).resolve().parents[2] / "shared" / "fonts"
BANGLA_FONT_PATH = FONT_DIR / "NotoSansBengali-Regular.ttf"

PAGE_WIDTH, PAGE_HEIGHT = 595.0, 842.0  # A4 in points
MARGIN = 50.0
FONT_SIZE = 11.0
LINE_HEIGHT = 16.0
PARAGRAPH_GAP = 6.0

_BENGLA_RANGE = ("\u0980", "\u09FF")


def _contains_bangla(text: str) -> bool:
    lo, hi = _BENGLA_RANGE
    return any(lo <= ch <= hi for ch in text)


def _wrap_line(text: str, font: pymupdf.Font, max_width: float) -> list[str]:
    if not text.strip():
        return [""]
    words = text.split()
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.text_length(candidate, fontsize=FONT_SIZE) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _write_line(page: pymupdf.Page, y: float, line: str) -> None:
    if _contains_bangla(line):
        page.insert_text(
            (MARGIN, y), line, fontsize=FONT_SIZE,
            fontname="beng", fontfile=str(BANGLA_FONT_PATH),
        )
    else:
        page.insert_text((MARGIN, y), line, fontsize=FONT_SIZE, fontname="helv")


def build_pdf(pages: list[str]) -> bytes:
    doc = pymupdf.open()
    font_regular = pymupdf.Font("helv")
    max_width = PAGE_WIDTH - 2 * MARGIN
    try:
        for text in pages:
            page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            y = MARGIN + FONT_SIZE
            for paragraph in text.split("\n"):
                for line in _wrap_line(paragraph, font_regular, max_width):
                    if y > PAGE_HEIGHT - MARGIN:
                        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
                        y = MARGIN + FONT_SIZE
                    _write_line(page, y, line)
                    y += LINE_HEIGHT
                y += PARAGRAPH_GAP
        return doc.tobytes(garbage=4, deflate=True)
    finally:
        doc.close()