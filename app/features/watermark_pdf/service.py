"""Service layer for applying watermarks to PDF documents."""

import logging
import pymupdf

from app.features.translate_pdf.pdf_generator import ensure_bangla_font

_BENGLA_RANGE = ("\u0980", "\u09FF")


def _contains_bangla(text: str) -> bool:
    lo, hi = _BENGLA_RANGE
    return any(lo <= ch <= hi for ch in text)


logger = logging.getLogger("pdf_editor")

DEFAULT_FONT_SIZE = 18.0
MARGIN = 36.0  # 0.5 inch margin in points


def _calculate_position(
    position: str,
    page_width: float,
    page_height: float,
    text_width: float,
    font_size: float = DEFAULT_FONT_SIZE,
    margin: float = MARGIN,
) -> tuple[float, float]:
    """Calculate the (x, y) baseline insertion point for text based on position code."""
    pos = position.lower()

    if pos == "top-left":
        x = margin
        y = margin + font_size
    elif pos == "top-center":
        x = max(margin, (page_width - text_width) / 2.0)
        y = margin + font_size
    elif pos == "top-right":
        x = max(margin, page_width - margin - text_width)
        y = margin + font_size
    elif pos == "center":
        x = max(margin, (page_width - text_width) / 2.0)
        y = (page_height + font_size) / 2.0
    elif pos == "bottom-left":
        x = margin
        y = page_height - margin
    elif pos == "bottom-center":
        x = max(margin, (page_width - text_width) / 2.0)
        y = page_height - margin
    elif pos == "bottom-right":
        x = max(margin, page_width - margin - text_width)
        y = page_height - margin
    else:
        # Default fallback to center
        x = max(margin, (page_width - text_width) / 2.0)
        y = (page_height + font_size) / 2.0

    return (x, y)


def apply_watermark(
    pdf_bytes: bytes,
    text: str,
    position: str,
    opacity: float,
    color: tuple[float, float, float],
    font_size: float = DEFAULT_FONT_SIZE,
) -> bytes:
    """Overlay watermark text on every page of the provided PDF document."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    is_bangla = _contains_bangla(text)
    font_path = ensure_bangla_font() if is_bangla else None

    # Measure text width
    if is_bangla and font_path and font_path.exists():
        font = pymupdf.Font(fontfile=str(font_path))
    else:
        font = pymupdf.Font("helv")

    text_width = font.text_length(text, fontsize=font_size)

    try:
        for page in doc:
            rect = page.rect
            x, y = _calculate_position(
                position=position,
                page_width=rect.width,
                page_height=rect.height,
                text_width=text_width,
                font_size=font_size,
            )

            kwargs = {
                "fontsize": font_size,
                "color": color,
                "fill_opacity": opacity,
            }
            if is_bangla and font_path and font_path.exists():
                kwargs["fontname"] = "beng"
                kwargs["fontfile"] = str(font_path)
            else:
                kwargs["fontname"] = "helv"

            page.insert_text((x, y), text, **kwargs)

        logger.info(
            "Applied watermark '%s' at position '%s' to %d page(s)",
            text,
            position,
            len(doc),
        )
        return doc.tobytes(garbage=4, deflate=True)
    finally:
        doc.close()
