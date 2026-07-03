"""Classify a page as vector (real CAD export) or raster (scan/flattened).

Vector pages expose real drawing primitives via get_drawings() and/or
positioned text spans via get_text(). Raster pages are typically a single
full-page embedded image with neither.
"""
from __future__ import annotations

from typing import Literal

import fitz

from ..config import settings

PageType = Literal["vector", "raster"]


def classify_page(page: fitz.Page) -> PageType:
    drawings = page.get_drawings()
    if len(drawings) >= settings.min_vector_drawings:
        return "vector"

    text = page.get_text("text").strip()
    if text:
        # real positioned text but few drawings — still vector content
        return "vector"

    return "raster"
