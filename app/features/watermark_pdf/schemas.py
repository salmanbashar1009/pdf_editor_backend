"""Schemas and field validators for POST /editor/pdf/watermark."""

import re
from fastapi import HTTPException

ALLOWED_POSITIONS = frozenset(
    {
        "top-left",
        "top-center",
        "top-right",
        "center",
        "bottom-left",
        "bottom-center",
        "bottom-right",
    }
)

HEX_COLOR_PATTERN = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def parse_text(value: str | None) -> str:
    """Validate that text is provided and non-empty."""
    if value is None or not value.strip():
        raise HTTPException(status_code=422, detail="Missing required field: text")
    return value.strip()


def parse_position(value: str | None) -> str:
    """Validate position against ALLOWED_POSITIONS."""
    if value is None or not value.strip():
        raise HTTPException(status_code=422, detail="Missing required field: position")
    pos = value.strip().lower()
    if pos not in ALLOWED_POSITIONS:
        raise HTTPException(status_code=422, detail=f"Invalid position code: {pos}")
    return pos


def parse_opacity(value: float | str | None) -> float:
    """Validate opacity as a float between 0.0 and 1.0 inclusive."""
    if value is None:
        raise HTTPException(status_code=422, detail="Missing required field: opacity")
    try:
        val = float(value)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Opacity must be a valid float number")
    if not (0.0 <= val <= 1.0):
        raise HTTPException(status_code=422, detail="Opacity must be between 0.0 and 1.0")
    return val


def parse_color(value: str | None) -> tuple[float, float, float]:
    """Validate hex color string (#RGB or #RRGGBB) and return (r, g, b) float tuple in 0.0..1.0."""
    if value is None or not value.strip():
        raise HTTPException(status_code=422, detail="Missing required field: color")
    color_str = value.strip()
    if not HEX_COLOR_PATTERN.match(color_str):
        raise HTTPException(status_code=422, detail=f"Invalid color format: {color_str}")

    hex_digits = color_str[1:]
    if len(hex_digits) == 3:
        r = int(hex_digits[0] * 2, 16) / 255.0
        g = int(hex_digits[1] * 2, 16) / 255.0
        b = int(hex_digits[2] * 2, 16) / 255.0
    else:
        r = int(hex_digits[0:2], 16) / 255.0
        g = int(hex_digits[2:4], 16) / 255.0
        b = int(hex_digits[4:6], 16) / 255.0
    return (r, g, b)
