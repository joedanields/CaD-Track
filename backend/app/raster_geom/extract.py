"""Approximate geometry extraction for comparisons involving raster inputs.

The drawing's ink is decomposed into connected components (clusters of
touching dark pixels); each component becomes an Entity with a normalized
bbox, centroid, and its share of the page's total ink. The diff itself
remains structural entity matching — no pixel mask or image alignment is
ever compared.

Connected-component labeling is deterministic: identical drawing regions
produce identical entities on both sides and match exactly, while genuinely
added or removed structures have no counterpart. Ink *share* (rather than
absolute pixel counts) makes the signature robust to systematic line-width
differences between a rendered vector page and a scan.

When either input is raster, BOTH sides are traced from their rendered pages
so the matcher compares like with like. Known text areas are masked out
first (each side using its own text entities) so glyph strokes don't
masquerade as drawing geometry — text is diffed separately.
"""
from __future__ import annotations

import uuid

import fitz
import numpy as np
from skimage.measure import label, regionprops

from ..config import settings
from ..models.diff_result import BBox, Entity, EntityKind


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

    total_ink = int(ink.sum())
    if total_ink == 0:
        return []

    labeled = label(ink, connectivity=2)
    entities: list[Entity] = []
    for prop in regionprops(labeled):
        if prop.area < settings.min_component_px:
            continue  # speckle / scan noise
        r0, c0, r1, c1 = prop.bbox
        bbox = (c0 / w, r0 / h, c1 / w, r1 / h)
        span = ((bbox[2] - bbox[0]) ** 2 + (bbox[3] - bbox[1]) ** 2) ** 0.5
        if span < settings.min_entity_span:
            continue
        cy, cx = prop.centroid
        # ink share in basis points; scale-free so a thick scan and a thin
        # vector render of the same structure still look alike
        ink_share = max(1, round(prop.area / total_ink * 10000))
        entities.append(
            Entity(
                id=uuid.uuid4().hex[:12],
                kind=EntityKind.GEOMETRY,
                bbox=bbox,
                centroid=(cx / w, cy / h),
                shape_signature={"ink": ink_share},
                confidence=settings.trace_confidence,
            )
        )
    return entities
