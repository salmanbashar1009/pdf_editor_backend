# Python + Flutter Developer — PDF Editor Backend API

FastAPI backend providing PDF processing utilities:
1. **API A — PDF Language Translator (`POST /api/translate-pdf`)**
2. **API B — PDF Watermark (`POST /editor/pdf/watermark`)**

---

## 🚀 Quick Start & Setup

### 1. Local Python Environment

#### Prerequisites
- Python 3.12+

#### Installation & Execution
```bash
# 1. Clone repository & enter project folder
cd pdf-editor-backend

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start FastAPI server with hot-reload
uvicorn app.main:app --reload --port 8000
```
Server will run at: **`http://127.0.0.1:8000`**  
Interactive Swagger API Docs: **`http://127.0.0.1:8000/docs`**

---

### 2. Docker & Docker Compose Setup

```bash
# Build and launch container in background
docker compose up --build -d

# Verify container health
curl http://localhost:8000/health
```

---

## 📡 API Reference & Documentation

### 1. API A — PDF Language Translator

**Endpoint**: `POST /api/translate-pdf`  
**Content-Type**: `multipart/form-data`

#### Required Form Fields
| Field | Type | Description |
|---|---|---|
| `file` | File Binary | Source PDF file (Max 10 MB) |
| `source_language` | String | ISO 639-1 language code (e.g. `en`) |
| `target_language` | String | ISO 639-1 language code (e.g. `bn`) |

*Supported Language Codes*: `en, bn, es, fr, de, hi, ar, pt, ru, ja, ko, zh, it, nl, tr, ur`.

#### Example cURL Command
```bash
curl -X POST "http://localhost:8000/api/translate-pdf" \
  -F "file=@document.pdf;type=application/pdf" \
  -F "source_language=en" \
  -F "target_language=bn" \
  --output translated_document.pdf
```

---

### 2. API B — PDF Watermark

**Endpoint**: `POST /editor/pdf/watermark`  
**Content-Type**: `multipart/form-data`

#### Required Form Fields
| Field | Type | Description / Allowed Values |
|---|---|---|
| `file` | File Binary | Source PDF file (Max 10 MB) |
| `text` | String | Watermark text (e.g. `CONFIDENTIAL`) |
| `position` | String | `top-left`, `top-center`, `top-right`, `center`, `bottom-left`, `bottom-center`, `bottom-right` |
| `opacity` | Number | Float between `0.0` and `1.0` (e.g. `0.25`) |
| `color` | String | Hex color string (e.g. `#FF0000`) |

#### Example cURL Command
```bash
curl -X POST "http://localhost:8000/editor/pdf/watermark" \
  -F "file=@document.pdf;type=application/pdf" \
  -F "text=CONFIDENTIAL" \
  -F "position=center" \
  -F "opacity=0.5" \
  -F "color=#FF0000" \
  --output watermarked_document.pdf
```

---

## 🧪 Testing with Postman

A ready-to-import Postman Collection is included in the project root:  
📄 **[`pdf_editor_api.postman_collection.json`](file:///d:/interview-task/graphic-cycle-python-flutter/pdf-editor-backend/pdf_editor_api.postman_collection.json)**

### How to Import & Use in Postman:
1. Open Postman $\rightarrow$ Click **Import**.
2. Select `pdf_editor_api.postman_collection.json`.
3. Open any request (`API A - Translate PDF` or `API B - Watermark PDF`).
4. Go to **Body** tab $\rightarrow$ **form-data** $\rightarrow$ select a PDF file for `file`.
5. Click **Send** $\rightarrow$ Click **Save Response / Save to a file** to inspect output.

---

## 🧪 Running Automated Tests

Run the full `pytest` test suite:
```bash
pytest tests/ -v
```
All 33 test cases cover translation, watermarking, security validation, and API integration.

---

## 📝 Design Choices Write-up

### 1. Core Libraries & Frameworks
- **FastAPI & Uvicorn**: High-performance, asynchronous REST framework with auto-generated OpenAPI / Swagger docs.
- **PyMuPDF (`fitz`)**: Lightweight, C-compiled PDF engine used for high-speed text extraction and document creation.
- **httpx**: Async HTTP client for keyless translation API requests.
- **Pydantic**: Type validation, configuration settings, and strict form input validation.

### 2. Handling Bangla (`bn`) Unicode & Joint Letters (যুক্তবর্ণ - Yuktoborno)
- **HarfBuzz Complex Text Layout (CTL) Shaping**: PyMuPDF's standard text insertion (`insert_text`) renders characters sequentially, which breaks Indic/Bengali conjunct glyphs (e.g. `ক`+`্`+`ষ` $\rightarrow$ `ক্ষ`). To solve this, `build_pdf` uses PyMuPDF's HTML/CSS layout engine (`insert_htmlbox`), which executes **HarfBuzz OpenType font shaping**.
- **Bundled Font**: `NotoSansBengali-Regular.ttf` is vendored under `app/shared/fonts/` (and automatically downloaded via CDN fallback if absent), ensuring proper glyph rendering across Docker/Linux environments without requiring OS system fonts.

### 3. Translation Provider Architecture
- Implemented a protocol-based `Translator` abstraction (`MyMemoryTranslator` & `GoogleTranslateTranslator`).
- `FallbackTranslator` intercepts daily free-tier rate limits (`429`) from MyMemory and seamlessly routes requests to Google Translate's keyless web endpoint, preventing service interruption.

### 4. Known Limitations
- **Layout Reflow**: The translation endpoint extracts text and reflows translated paragraphs into a newly formatted PDF. It does not preserve fixed coordinate-bound shapes or embedded raster images.
- **Single PDF Processing**: Processing is optimized for synchronous single-file API requests (< 10MB).
