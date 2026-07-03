"""Pipeline orchestration: classify -> extract -> match -> classify -> stats -> summary.

The comparison mode is decided by what both inputs can provide:
- both vector      -> geometry + text entities are diffed ("geometry+text")
- any raster input -> both sides reduced to TEXT entities only ("text-only"),
                      the vector side using its exact text spans and the
                      raster side using OCR. Comparing vector geometry against
                      a side that has none would report everything as removed.
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
from ..stats.aggregate import compute_stats
from ..summary.generator import generate_summary
from ..vector.extract import extract_primitives, extract_text_spans
from ..vector.group import group_into_entities, text_spans_to_entities


@dataclass
class CompareResult:
    diff: DiffResult
    stats: StatsSummary
    summary: str


def _extract_entities(page: fitz.Page, page_type: str, text_only: bool) -> list[Entity]:
    if page_type == "vector":
        entities = text_spans_to_entities(extract_text_spans(page))
        if not text_only:
            entities += group_into_entities(extract_primitives(page))
        return entities
    return extract_text_entities(page)  # OCR path


def run_comparison(job_id: str, path_a: Path, path_b: Path) -> CompareResult:
    doc_a = load_input(path_a)
    doc_b = load_input(path_b)
    try:
        page_a, page_b = doc_a.page, doc_b.page
        type_a = classify_page(page_a)
        type_b = classify_page(page_b)

        text_only = "raster" in (type_a, type_b)
        notes: list[str] = []
        if text_only:
            raster_side = "A" if type_a == "raster" else "B"
            if type_a == "raster" and type_b == "raster":
                raster_side = "both inputs"
            notes.append(
                f"Raster input detected ({raster_side}): no vector data available, "
                "comparison restricted to text/annotations extracted via OCR."
            )

        entities_a = _extract_entities(page_a, type_a, text_only)
        entities_b = _extract_entities(page_b, type_b, text_only)

        pairs = match_entities(entities_a, entities_b)
        regions = classify_matches(pairs)

        diff = DiffResult(
            job_id=job_id,
            path_a=type_a,
            path_b=type_b,
            compare_mode="text-only" if text_only else "geometry+text",
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
