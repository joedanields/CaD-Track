"""Classify matched entity pairs into added/removed/moved/modified regions."""
from __future__ import annotations

import uuid

from ..config import settings
from ..models.diff_result import ChangeType, Entity, EntityKind, Region
from .match import MatchPair, compatibility


def _area(bbox: tuple[float, float, float, float]) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def _label(e: Entity) -> str:
    if e.kind == EntityKind.TEXT:
        return f"text: '{e.text}'"
    return f"geometry ({e.primitive_count} segment{'s' if e.primitive_count != 1 else ''})"


def _region(
    entity: Entity,
    change_type: ChangeType,
    detail: str | None = None,
    old_bbox: tuple[float, float, float, float] | None = None,
    confidence: float | None = None,
) -> Region:
    return Region(
        id=uuid.uuid4().hex[:12],
        change_type=change_type,
        kind=entity.kind,
        bbox=entity.bbox,
        centroid=entity.centroid,
        area_fraction=_area(entity.bbox),
        confidence=confidence if confidence is not None else entity.confidence,
        label=_label(entity),
        detail=detail,
        old_bbox=old_bbox,
    )


def classify_matches(pairs: list[MatchPair]) -> list[Region]:
    regions: list[Region] = []
    for pair in pairs:
        if pair.old is not None and pair.new is None:
            regions.append(_region(pair.old, ChangeType.REMOVED))
            continue
        if pair.old is None and pair.new is not None:
            regions.append(_region(pair.new, ChangeType.ADDED))
            continue

        old, new = pair.old, pair.new
        assert old is not None and new is not None
        conf = min(old.confidence, new.confidence)
        # traced/OCR entities carry jitter: require larger displacement and a
        # bigger similarity drop before flagging a change
        exact = conf >= 1.0

        moved = pair.distance > (settings.moved_tol if exact else settings.approx_moved_tol)
        if old.kind == EntityKind.TEXT:
            content_changed = (old.text or "") != (new.text or "")
        else:
            threshold = 0.98 if exact else settings.approx_modified_compat
            content_changed = compatibility(old, new) < threshold

        if content_changed:
            detail = (
                f"'{old.text}' -> '{new.text}'"
                if old.kind == EntityKind.TEXT
                else "geometry altered"
            )
            regions.append(
                _region(new, ChangeType.MODIFIED, detail=detail, old_bbox=old.bbox, confidence=conf)
            )
        elif moved:
            regions.append(
                _region(new, ChangeType.MOVED, old_bbox=old.bbox, confidence=conf)
            )
        # matched, same content, same position -> unchanged, no region
    return regions
