"""Approximate geometry extraction for comparisons involving raster inputs.

The drawing's ink is traced into straight line segments (probabilistic Hough
transform on the binarized page) which become the same Primitive/Entity
objects the exact vector path produces. The diff itself remains structural
entity matching — no pixel mask or image alignment is ever compared.

When either input is raster, BOTH sides are traced from their rendered pages
so the matcher compares like with like: identical drawing regions trace into
similar segment clusters on both sides and match, while genuinely added or
removed structures have no counterpart.

Known text areas are masked out before tracing (each side using its own text
entities) so glyph strokes don't masquerade as drawing geometry — text is
diffed separately and exactly/via OCR.
"""
from __future__ import annotations

import fitz
import numpy as np
from skimage.transform import probabilistic_hough_line

from ..config import settings
from ..models.diff_result import BBox, Entity
from ..vector.extract import Primitive
from ..vector.group import group_into_entities


def _page_to_gray(page: fitz.Page, dpi: int) -> np.ndarray:
    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy()


def extract_geometry_entities(
    page: fitz.Page, text_bboxes: list[BBox]
) -> list[Entity]:
    gray = _page_to_gray(page, settings.trace_dpi)
    h, w = gray.shape
    ink = gray < settings.ink_threshold

    # mask out known text areas (normalized bboxes -> pixels, small padding)
    pad = max(1, int(0.002 * max(w, h)))
    for x0, y0, x1, y1 in text_bboxes:
        r0 = max(0, int(y0 * h) - pad)
        r1 = min(h, int(y1 * h) + pad)
        c0 = max(0, int(x0 * w) - pad)
        c1 = min(w, int(x1 * w) + pad)
        ink[r0:r1, c0:c1] = False

    min_len = max(5, int(settings.hough_line_length_frac * max(w, h)))
    segments = probabilistic_hough_line(
        ink,
        threshold=settings.hough_threshold,
        line_length=min_len,
        line_gap=settings.hough_line_gap,
    )

    primitives = [
        Primitive(kind="l", points=[(x0 / w, y0 / h), (x1 / w, y1 / h)])
        for (x0, y0), (x1, y1) in segments
    ]
    entities = group_into_entities(primitives, tol=settings.trace_join_tol)

    kept: list[Entity] = []
    for e in entities:
        span = ((e.bbox[2] - e.bbox[0]) ** 2 + (e.bbox[3] - e.bbox[1]) ** 2) ** 0.5
        if span < settings.min_entity_span:
            continue  # tracing noise
        e.confidence = settings.trace_confidence
        kept.append(e)
    return kept
