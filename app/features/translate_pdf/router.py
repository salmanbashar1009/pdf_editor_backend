"""Thin router for POST /api/translate-pdf."""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile

from app.core.config import Settings, get_settings
from app.core.security import read_upload, sanitize_filename, validate_pdf_bytes
from app.features.translate_pdf.schemas import parse_language
from app.features.translate_pdf.service import get_translator, translate_pdf
from app.features.translate_pdf.translator import Translator

router = APIRouter(tags=["translate"])
logger = logging.getLogger("pdf_editor")


@router.post("/api/translate-pdf")
def translate_pdf_endpoint(
    file: UploadFile | None = File(None),
    source_language: str | None = Form(None),
    target_language: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    translator: Translator = Depends(get_translator),
) -> Response:
    if file is None or not file.filename:
        raise HTTPException(status_code=422, detail="Missing required field: file")
    source = parse_language(source_language, "source_language")
    target = parse_language(target_language, "target_language")
    if source == target:
        raise HTTPException(status_code=400, detail="source_language and target_language must differ")

    data = read_upload(file, settings.max_upload_size)
    validate_pdf_bytes(data)
    output = translate_pdf(data, source, target, translator)

    stem = sanitize_filename(file.filename).rsplit(".", 1)[0]
    filename = f"translated_{stem}_{source}_to_{target}.pdf"
    return Response(
        content=output,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )