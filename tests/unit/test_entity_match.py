"""Core diff-engine test: one added, one removed, one moved, one modified."""
from app.entity_match.classify import classify_matches
from app.entity_match.match import match_entities
from app.models.diff_result import ChangeType, Entity, EntityKind


def _text(id_, x, y, text):
    return Entity(
        id=id_,
        kind=EntityKind.TEXT,
        bbox=(x - 0.02, y - 0.01, x + 0.02, y + 0.01),
        centroid=(x, y),
        text=text,
    )


def _geom(id_, x, y, signature=None, count=4):
    return Entity(
        id=id_,
        kind=EntityKind.GEOMETRY,
        bbox=(x - 0.05, y - 0.05, x + 0.05, y + 0.05),
        centroid=(x, y),
        shape_signature=signature or {"l": count},
        primitive_count=count,
    )


def test_added_removed_moved_modified():
    old = [
        _text("t1", 0.20, 0.20, "R10"),        # will be modified -> "R15"
        _text("t2", 0.50, 0.50, "SCALE 1:8"),  # unchanged
        _geom("g1", 0.80, 0.20),               # will be removed
        _geom("g2", 0.30, 0.80),               # will be moved
    ]
    new = [
        _text("t1n", 0.20, 0.20, "R15"),
        _text("t2n", 0.50, 0.50, "SCALE 1:8"),
        _geom("g2n", 0.33, 0.80),              # moved by 0.03 (> moved_tol)
        _geom("g3", 0.60, 0.60),               # added
    ]

    regions = classify_matches(match_entities(old, new))
    by_type = {r.change_type: r for r in regions}

    assert len(regions) == 4
    assert by_type[ChangeType.MODIFIED].detail == "'R10' -> 'R15'"
    assert by_type[ChangeType.REMOVED].kind == EntityKind.GEOMETRY
    assert by_type[ChangeType.MOVED].old_bbox is not None
    assert by_type[ChangeType.ADDED].centroid == (0.60, 0.60)


def test_identical_inputs_yield_no_regions():
    ents = [_text("a", 0.3, 0.3, "NOTE 1"), _geom("b", 0.7, 0.7)]
    regions = classify_matches(match_entities(ents, ents))
    assert regions == []


def test_global_shift_within_radius_is_not_total_change():
    """The original bug: a small uniform offset must not flag everything.

    Every entity is shifted by 1% of the page — matching still pairs them
    up (they land within the search radius) and classifies them as moved,
    NOT as unrelated added+removed pairs.
    """
    old = [_text(f"o{i}", 0.1 * i, 0.1 * i, f"LBL{i}") for i in range(1, 8)]
    new = [_text(f"n{i}", 0.1 * i + 0.01, 0.1 * i + 0.01, f"LBL{i}") for i in range(1, 8)]
    regions = classify_matches(match_entities(old, new))
    assert all(r.change_type == ChangeType.MOVED for r in regions)
    assert len(regions) == 7  # everything matched, nothing added/removed
