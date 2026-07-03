# CaD-Track

Git-style change tracking for CAD drawings. Upload two versions (v1/v2) of the
same drawing — PDF, PNG, or JPG — and get back the changes as **added /
removed / moved / modified** regions, an annotated visualization, statistics,
and a plain-English summary.

Unlike pixel-based diff tools, CaD-Track contains **no pixel-comparison
algorithm**: it extracts the structured content of each drawing (vector
geometry and text via PyMuPDF for native CAD exports, OCR text via Tesseract
for scans) and diffs those entities directly. A global page shift, rescale,
or DPI difference therefore cannot make the whole sheet read as "changed."

See [docs/architecture.md](docs/architecture.md) for the full design and
[docs/requirements.md](docs/requirements.md) for the original requirements.

## Features

- Accepts PDF (vector or scanned), PNG, JPG — auto-detects vector vs raster.
- Vector PDFs: exact geometry + text diff (primitives grouped into entities,
  matched by position and shape).
- Raster inputs: text/annotation diff via OCR, with explicit warnings when a
  scan is too low-resolution to read reliably.
- Change overlay, side-by-side view, per-region stats table, % area changed.
- Rule-based natural-language summary (no LLM, fully offline).

## Setup

Requirements: Python 3.11+, [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
(Windows: `winget install UB-Mannheim.TesseractOCR`; the backend finds the
default install path automatically).

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 — the web UI is served at the root; interactive
API docs at `/docs`.

## Usage

1. Drop the old version into "Drawing A" and the new version into "Drawing B".
2. Click **Compare**.
3. Review the change overlay (green = added, red = removed, amber = moved,
   blue = modified), the statistics table, and the generated summary.

Sample inputs live in [samples/real_pair/](samples/real_pair/).

### API

```
POST /api/upload                 multipart file_a, file_b -> { job_id }
POST /api/compare/{job_id}       run the comparison
GET  /api/jobs/{job_id}          status + diff + stats + summary
GET  /api/jobs/{job_id}/visualization?mode=bbox|side_by_side|original_a|original_b
GET  /api/jobs/{job_id}/summary
GET  /api/jobs/{job_id}/stats
DELETE /api/jobs/{job_id}
```

## Tests

```bash
python -m pytest tests
```

Unit tests cover the matcher, stats math, and location/severity bucketing;
integration tests run the full pipeline on synthetic vector-PDF and raster
pairs with known expected diffs, plus a smoke test on the real sample pair.

## Limitations (v1)

- Raster inputs are compared by text/annotations only — geometry changes in
  scans are not detected (by design; no pixel diffing).
- Single page: page 1 of each document is compared.
- Job store is in-memory; restart clears results.
