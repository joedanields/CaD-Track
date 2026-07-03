"""OCR extraction path for raster-only pages (scans / flattened images).

Produces TEXT entities only — there is no vector data to recover, so
geometry changes on pure-raster pages are out of scope by design (the diff
engine works on structured entities, never on pixels).
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

# locate the tesseract binary when it isn't on PATH (default Windows installs)
if shutil.which("tesseract") is None:
    for candidate in (
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path.home() / r"AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ):
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            break

from ..config import settings
from ..models.diff_result import Entity, EntityKind


def rasterize_page(page: fitz.Page, dpi: int | None = None) -> Image.Image:
    dpi = dpi or settings.ocr_dpi
    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    return Image.frombytes("L", (pix.width, pix.height), pix.samples)


def extract_text_entities(page: fitz.Page) -> list[Entity]:
    img = rasterize_page(page)
    w, h = img.size
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    entities: list[Entity] = []
    for i, raw in enumerate(data["text"]):
        text = (raw or "").strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1.0
        if conf < settings.min_ocr_confidence:
            continue
        x, y = data["left"][i], data["top"][i]
        bw, bh = data["width"][i], data["height"][i]
        bbox = (x / w, y / h, (x + bw) / w, (y + bh) / h)
        entities.append(
            Entity(
                id=uuid.uuid4().hex[:12],
                kind=EntityKind.TEXT,
                bbox=bbox,
                centroid=((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2),
                text=text,
                confidence=conf / 100.0,
            )
        )
    return entities
