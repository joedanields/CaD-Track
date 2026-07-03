# CaD-Track

CAD drawing version diff ("git for drawings"): structured entity diffing of
vector geometry + text/annotations. **No pixel/CV comparison anywhere in the
diff logic** — this is a hard project constraint; do not reintroduce SSIM,
absdiff, ORB/homography, or any image-alignment step.

## Layout

- `backend/app/` — FastAPI backend; pipeline in `pipeline/compare.py`,
  matcher in `entity_match/`, thresholds in `config.py`.
- `frontend/` — plain HTML/JS served by the backend at `/`.
- `tests/` — pytest; `tests/conftest.py` adds `backend/` to `sys.path`.
- `samples/real_pair/` — real v1 (vector) / v2 (low-res raster) sample pair.
- `docs/architecture.md` — design rationale and diagrams.

## Commands

- Run server: `cd backend && python -m uvicorn app.main:app --reload`
- Tests: `python -m pytest tests` (from repo root)

## Notes

- All coordinates normalized to [0,1] per page — never compare raw pixel/pt
  coordinates across documents.
- Raster inputs are diffed by OCR text only (Tesseract); this is by design.
- Windows: Tesseract lives at `C:\Program Files\Tesseract-OCR\`;
  `ocr/extract.py` auto-detects it when not on PATH.
