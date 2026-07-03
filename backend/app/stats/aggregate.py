"""Aggregate diff regions into the FR-5 statistics summary."""
from __future__ import annotations

from ..models.diff_result import ChangeType, DiffResult
from ..models.schemas import RegionStat, StatsSummary
from ..summary.location import bucket_location


def _union_area(boxes: list[tuple[float, float, float, float]]) -> float:
    """Union of axis-aligned bbox areas via coordinate-grid sweep.

    Rect-level (not pixel-mask) computation: build the grid of unique x/y
    edges and sum covered cells, so overlapping regions aren't double-counted.
    """
    if not boxes:
        return 0.0
    xs = sorted({v for b in boxes for v in (b[0], b[2])})
    ys = sorted({v for b in boxes for v in (b[1], b[3])})
    total = 0.0
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx = (xs[i] + xs[i + 1]) / 2
            cy = (ys[j] + ys[j + 1]) / 2
            if any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in boxes):
                total += (xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j])
    return total


def compute_stats(diff: DiffResult) -> StatsSummary:
    counts = {ct: 0 for ct in ChangeType}
    for region in diff.regions:
        counts[region.change_type] += 1

    per_region = [
        RegionStat(
            id=r.id,
            change_type=r.change_type.value,
            kind=r.kind.value,
            location=bucket_location(*r.centroid),
            area_fraction=round(r.area_fraction, 6),
            bbox=r.bbox,
            label=r.label,
            detail=r.detail,
        )
        for r in sorted(diff.regions, key=lambda r: r.area_fraction, reverse=True)
    ]

    return StatsSummary(
        total_regions=len(diff.regions),
        added_count=counts[ChangeType.ADDED],
        removed_count=counts[ChangeType.REMOVED],
        moved_count=counts[ChangeType.MOVED],
        modified_count=counts[ChangeType.MODIFIED],
        total_changed_area_fraction=round(
            _union_area([r.bbox for r in diff.regions]), 6
        ),
        per_region=per_region,
    )
