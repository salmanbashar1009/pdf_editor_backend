"""PDF Generator with automatic Unicode, HarfBuzz font shaping, and Bengali joint letter support."""

import html
import logging
from pathlib import Path
import pymupdf

logger = logging.getLogger("pdf_editor")

FONT_DIR = Path(__file__).resolve().parents[2] / "shared" / "fonts"
BANGLA_FONT_PATH = FONT_DIR / "NotoSansBengali-Regular.ttf"

PAGE_WIDTH, PAGE_HEIGHT = 595.0, 842.0  # A4 in points
MARGIN = 50.0
FONT_SIZE = 11.0


def ensure_bangla_font() -> Path | None:
    """Ensure Bengali font file exists locally; download or fallback if missing."""
    if BANGLA_FONT_PATH.exists():
        return BANGLA_FONT_PATH

    FONT_DIR.mkdir(parents=True, exist_ok=True)
    # 1. Download Noto Sans Bengali font from Google Fonts CDN
    url = "https://fonts.gstatic.com/s/notosansbengali/v33/Cn-SJsCGWQxOjaGwMQ6fIiMywrNJIky6nvd8BjzVMvJx2mcSPVFpVEqE-6KmsolLudA.ttf"
    try:
        import httpx
        try:
            r = httpx.get(url, timeout=10.0)
        except httpx.ConnectError:
            r = httpx.get(url, timeout=10.0, verify=False)
        if r.status_code == 200 and len(r.content) > 1000:
            BANGLA_FONT_PATH.write_bytes(r.content)
            logger.info("Downloaded NotoSansBengali-Regular.ttf to %s", BANGLA_FONT_PATH)
            return BANGLA_FONT_PATH
    except Exception as exc:
        logger.warning("Could not download Bengali font: %s", exc)

    # 2. Check for Windows system Indic font as local fallback
    for win_font in ["C:/Windows/Fonts/Nirmala.ttc", "C:/Windows/Fonts/vrinda.ttf"]:
        p = Path(win_font)
        if p.exists():
            return p

    return None


def build_pdf(pages: list[str]) -> bytes:
    """Build a PDF from text pages using MuPDF's HTML/CSS layout engine.
    
    Using insert_htmlbox enables HarfBuzz OpenType complex text layout (CTL) shaping,
    ensuring Bengali joint letters (Yukta-akshar / Yuktoborno) are rendered perfectly
    without broken glyphs.
    """
    doc = pymupdf.open()
    font_path = ensure_bangla_font()
    
    font_dir = font_path.parent if font_path else FONT_DIR
    font_filename = font_path.name if font_path else "NotoSansBengali-Regular.ttf"
    archive = pymupdf.Archive(str(font_dir))
    
    css = f"""
    @font-face {{
        font-family: 'NotoBengali';
        src: url('{font_filename}');
    }}
    body {{
        font-family: 'NotoBengali', 'Helvetica', 'Arial', sans-serif;
        font-size: 11pt;
        line-height: 1.5;
        color: #000000;
        margin: 0;
        padding: 0;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 8px;
        white-space: pre-wrap;
    }}
    """
    
    rect = pymupdf.Rect(MARGIN, MARGIN, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN)
    
    try:
        for text in pages:
            page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            paragraphs = [html.escape(p) for p in text.split("\n")]
            body_html = "".join(f"<p>{p}</p>" if p.strip() else "<br/>" for p in paragraphs)
            html_content = f"<div>{body_html}</div>"
            
            page.insert_htmlbox(rect, html_content, css=css, archive=archive)
            
        return doc.tobytes(garbage=4, deflate=True)
    finally:
        doc.close()