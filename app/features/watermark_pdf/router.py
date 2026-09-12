"""Router for POST /editor/pdf/watermark."""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile

from app.core.config import Settings, get_settings
from app.core.security import read_upload, sanitize_filename, validate_pdf_bytes
from app.features.watermark_pdf.schemas import (
    parse_color,
    parse_opacity,
    parse_position,
    parse_text,
)
from app.features.watermark_pdf.service import apply_watermark

router = APIRouter(tags=["watermark"])
logger = logging.getLogger("pdf_editor")


@router.post("/editor/pdf/watermark")
def watermark_pdf_endpoint(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    position: str | None = Form(None),
    opacity: str | float | None = Form(None),
    color: str | None = Form(None),
    settings: Settings = Depends(get_settings),
) -> Response:
    if file is None or not file.filename:
        raise HTTPException(status_code=422, detail="Missing required field: file")

    validated_text = parse_text(text)
    validated_position = parse_position(position)
    validated_opacity = parse_opacity(opacity)
    validated_color = parse_color(color)

    data = read_upload(file, settings.max_upload_size)
    validate_pdf_bytes(data)

    output = apply_watermark(
        pdf_bytes=data,
        text=validated_text,
        position=validated_position,
        opacity=validated_opacity,
        color=validated_color,
    )

    stem = sanitize_filename(file.filename).rsplit(".", 1)[0]
    filename = f"watermarked_{stem}.pdf"
    return Response(
        content=output,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
