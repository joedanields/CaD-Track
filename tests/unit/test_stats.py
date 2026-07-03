from app.models.diff_result import ChangeType, DiffResult, EntityKind, Region
from app.stats.aggregate import _union_area, compute_stats


def _region(id_, bbox, change_type):
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    return Region(
        id=id_,
        change_type=change_type,
        kind=EntityKind.GEOMETRY,
        bbox=bbox,
        centroid=(cx, cy),
        area_fraction=(bbox[2] - bbox[0]) * (bbox[3] - bbox[1]),
        confidence=1.0,
    )


def test_union_area_no_double_count():
    # two identical boxes -> union equals one box's area
    boxes = [(0.0, 0.0, 0.5, 0.5), (0.0, 0.0, 0.5, 0.5)]
    assert abs(_union_area(boxes) - 0.25) < 1e-9

    # disjoint boxes add up
    boxes = [(0.0, 0.0, 0.1, 0.1), (0.5, 0.5, 0.6, 0.6)]
    assert abs(_union_area(boxes) - 0.02) < 1e-9

    # 50% overlap
    boxes = [(0.0, 0.0, 0.2, 0.1), (0.1, 0.0, 0.3, 0.1)]
    assert abs(_union_area(boxes) - 0.03) < 1e-9


def test_compute_stats_counts_and_order():
    diff = DiffResult(
        job_id="t",
        path_a="vector",
        path_b="vector",
        compare_mode="geometry+text",
        page_width_a=100, page_height_a=100,
        page_width_b=100, page_height_b=100,
        regions=[
            _region("r1", (0.0, 0.0, 0.1, 0.1), ChangeType.ADDED),
            _region("r2", (0.5, 0.5, 0.9, 0.9), ChangeType.REMOVED),
            _region("r3", (0.2, 0.2, 0.25, 0.25), ChangeType.MOVED),
        ],
        entity_count_a=10,
        entity_count_b=10,
    )
    stats = compute_stats(diff)
    assert stats.total_regions == 3
    assert (stats.added_count, stats.removed_count, stats.moved_count) == (1, 1, 1)
    # per_region sorted by area desc -> the big removed box first
    assert stats.per_region[0].id == "r2"
    assert abs(stats.total_changed_area_fraction - (0.01 + 0.16 + 0.0025)) < 1e-6
