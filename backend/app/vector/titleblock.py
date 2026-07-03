"""Title-block isolation.

Engineering drawings conventionally place a metadata block (title, revision,
drawn-by, date, scale) in the bottom band or bottom-right corner. Entities
inside that region are compared as labeled metadata rather than as drawing
geometry, so recurring border/legend content doesn't pollute the diff.

MVP heuristic: the bottom-right region (bottom 15% band intersected with the
right 30% column) counts as title block when it contains a dense cluster of
short text spans.
"""
from __future__ import annotations

from ..models.diff_result import BBox, Entity, EntityKind

# normalized region: (x0, y0, x1, y1)
_TITLEBLOCK_CANDIDATE: BBox = (0.70, 0.85, 1.0, 1.0)
_MIN_SPANS_FOR_TITLEBLOCK = 3


def _inside(centroid: tuple[float, float], region: BBox) -> bool:
    x, y = centroid
    return region[0] <= x <= region[2] and region[1] <= y <= region[3]


def detect_titleblock_region(entities: list[Entity]) -> BBox | None:
    """Return the title-block bbox if the candidate corner is text-dense."""
    text_inside = [
        e
        for e in entities
        if e.kind == EntityKind.TEXT and _inside(e.centroid, _TITLEBLOCK_CANDIDATE)
    ]
    if len(text_inside) >= _MIN_SPANS_FOR_TITLEBLOCK:
        return _TITLEBLOCK_CANDIDATE
    return None


def split_titleblock(
    entities: list[Entity],
) -> tuple[list[Entity], list[Entity], BBox | None]:
    """Split entities into (drawing_body, titleblock_entities, region)."""
    region = detect_titleblock_region(entities)
    if region is None:
        return entities, [], None
    body = [e for e in entities if not _inside(e.centroid, region)]
    block = [e for e in entities if _inside(e.centroid, region)]
    return body, block, region
