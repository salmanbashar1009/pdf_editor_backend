"""FastAPI application factory for the PDF Editor backend."""

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import install_exception_handlers
from app.core.logging import configure_logging
from app.features.translate_pdf.router import router as translate_router
try:
    from app.features.watermark_pdf.router import router as watermark_router
except ImportError:  # Watermark feature not implemented yet
    from fastapi import APIRouter
    watermark_router = APIRouter()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="PDF Editor API", version="1.0.0")
    install_exception_handlers(app)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(translate_router)
    app.include_router(watermark_router)
    return app


app = create_app()