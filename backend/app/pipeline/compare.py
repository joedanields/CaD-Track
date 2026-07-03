"""Pipeline orchestration: classify -> extract -> match -> classify -> stats -> summary.

Comparison modes, decided by what both inputs can provide:

- both vector          -> "geometry+text": exact vector primitives + text spans.
- any raster involved  -> "approx-geometry+text": text comes from the vector
  side's exact spans and/or OCR on the raster side, while geometry on BOTH
  sides is traced into line segments from the rendered page (like-for-like),
  so drawing-design changes are detected even for scans — still via entity
  matching, never a pixel comparison.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz

from ..detect.classify import classify_page
from ..entity_match.classify import classify_matches
from ..entity_match.match import match_entities
from ..ingest.loader import load_input
from ..models.diff_result import DiffResult, Entity, EntityKind
from ..models.schemas import StatsSummary
from ..ocr.extract import extract_text_entities
from ..raster_geom.extract import extract_geometry_entities
from ..stats.aggregate import compute_stats
from ..summary.generator import generate_summary
from ..vector.extract import extract_primitives, extract_text_spans
from ..vector.group import group_into_entities, text_spans_to_entities


@dataclass
class CompareResult:
    diff: DiffResult
    stats: StatsSummary
    summary: str


def _extract_entities(page: fitz.Page, page_type: str, approx: bool) -> list[Entity]:
    # text: exact spans for vector pages, OCR words for raster pages
    if page_type == "vector":
        text_entities = text_spans_to_entities(extract_text_spans(page))
    else:
        text_entities = extract_text_entities(page)

    # geometry: exact primitives when both sides are vector, traced segments
    # (text areas masked) when any side is raster
    if approx:
        text_bboxes = [e.bbox for e in text_entities]
        geom_entities = extract_geometry_entities(page, text_bboxes)
    else:
        geom_entities = group_into_entities(extract_primitives(page))

    return text_entities + geom_entities


def run_comparison(job_id: str, path_a: Path, path_b: Path) -> CompareResult:
    doc_a = load_input(path_a)
    doc_b = load_input(path_b)
    try:
        page_a, page_b = doc_a.page, doc_b.page
        type_a = classify_page(page_a)
        type_b = classify_page(page_b)

        approx = "raster" in (type_a, type_b)
        notes: list[str] = []
        if approx:
            raster_side = "A" if type_a == "raster" else "B"
            if type_a == "raster" and type_b == "raster":
                raster_side = "both inputs"
            notes.append(
                f"Raster input detected ({raster_side}): geometry was compared "
                "approximately by tracing drawing lines from both rendered pages; "
                "text was compared via OCR on the raster side."
            )

        entities_a = _extract_entities(page_a, type_a, approx)
        entities_b = _extract_entities(page_b, type_b, approx)

        if approx:
            text_counts = {
                "A": sum(1 for e in entities_a if e.kind == EntityKind.TEXT),
                "B": sum(1 for e in entities_b if e.kind == EntityKind.TEXT),
            }
            low, high = min(text_counts.values()), max(text_counts.values())
            if high > 0 and low < 0.2 * high:
                sparse = min(text_counts, key=text_counts.get)
                notes.append(
                    f"Warning: input {sparse} yielded very few readable text "
                    f"elements ({low} vs {high}) — likely a low-resolution scan. "
                    "Text-change results are unreliable; most annotations will "
                    "appear as added/removed. Provide a higher-resolution scan "
                    "or a native vector PDF for a meaningful text comparison."
                )

        pairs = match_entities(entities_a, entities_b)
        regions = classify_matches(pairs)

        diff = DiffResult(
            job_id=job_id,
            path_a=type_a,
            path_b=type_b,
            compare_mode="approx-geometry+text" if approx else "geometry+text",
            page_width_a=page_a.rect.width,
            page_height_a=page_a.rect.height,
            page_width_b=page_b.rect.width,
            page_height_b=page_b.rect.height,
            regions=regions,
            entity_count_a=len(entities_a),
            entity_count_b=len(entities_b),
            notes=notes,
        )
        stats = compute_stats(diff)
        summary = generate_summary(diff, stats)
        return CompareResult(diff=diff, stats=stats, summary=summary)
    finally:
        doc_a.close()
        doc_b.close()
