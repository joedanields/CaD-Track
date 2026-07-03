"""Match entities between v1 and v2 of a drawing.

Nearest-neighbor assignment over normalized centroids (KD-tree), gated by a
compatibility check (text similarity for TEXT entities, shape-signature
similarity for GEOMETRY entities). Greedy one-to-one by ascending distance.

Because all coordinates are normalized, a global page shift/scale between
the two files does not create spurious mismatches the way pixel diffing did.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

import numpy as np
from scipy.spatial import cKDTree

from ..config import settings
from ..models.diff_result import Entity, EntityKind


@dataclass
class MatchPair:
    old: Optional[Entity]
    new: Optional[Entity]
    distance: float = 0.0


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _signature_similarity(a: Entity, b: Entity) -> float:
    """Similarity of primitive-kind histograms plus size agreement, 0..1."""
    kinds = set(a.shape_signature) | set(b.shape_signature)
    if not kinds:
        return 1.0
    overlap = sum(
        min(a.shape_signature.get(k, 0), b.shape_signature.get(k, 0)) for k in kinds
    )
    total = sum(
        max(a.shape_signature.get(k, 0), b.shape_signature.get(k, 0)) for k in kinds
    )
    hist_sim = overlap / total if total else 1.0

    area_a = (a.bbox[2] - a.bbox[0]) * (a.bbox[3] - a.bbox[1])
    area_b = (b.bbox[2] - b.bbox[0]) * (b.bbox[3] - b.bbox[1])
    if max(area_a, area_b) < 1e-12:
        size_sim = 1.0
    else:
        size_sim = min(area_a, area_b) / max(area_a, area_b)
    return 0.7 * hist_sim + 0.3 * size_sim


def compatibility(a: Entity, b: Entity) -> float:
    """0..1 score of whether a and b plausibly represent the same element."""
    if a.kind != b.kind:
        return 0.0
    if a.kind == EntityKind.TEXT:
        return _text_similarity(a.text or "", b.text or "")
    return _signature_similarity(a, b)


def match_entities(
    old: list[Entity],
    new: list[Entity],
    search_radius: float | None = None,
) -> list[MatchPair]:
    """Return matched pairs plus unmatched singletons from both sides."""
    radius = search_radius if search_radius is not None else settings.match_search_radius
    pairs: list[MatchPair] = []

    if not old or not new:
        pairs += [MatchPair(old=e, new=None) for e in old]
        pairs += [MatchPair(old=None, new=e) for e in new]
        return pairs

    tree = cKDTree(np.array([e.centroid for e in new]))
    k = min(8, len(new))
    candidates: list[tuple[float, int, int]] = []  # (cost, old_idx, new_idx)

    for i, e_old in enumerate(old):
        dists, idxs = tree.query(e_old.centroid, k=k)
        if k == 1:
            dists, idxs = [dists], [idxs]
        for dist, j in zip(dists, idxs):
            if dist > radius:
                continue
            e_new = new[int(j)]
            compat = compatibility(e_old, e_new)
            if e_old.kind == EntityKind.TEXT:
                # an annotation at (nearly) the same position is the same
                # slot even when its value changed (e.g. "R10" -> "R15"),
                # so proximity relaxes the required text similarity
                min_compat = 0.2 if dist <= settings.moved_tol else settings.text_match_ratio
            else:
                min_compat = 0.5
            if compat < min_compat:
                continue
            # lower cost = closer and more similar
            cost = dist + (1.0 - compat) * radius
            candidates.append((cost, i, int(j)))

    candidates.sort()
    used_old: set[int] = set()
    used_new: set[int] = set()
    for cost, i, j in candidates:
        if i in used_old or j in used_new:
            continue
        used_old.add(i)
        used_new.add(j)
        dx = old[i].centroid[0] - new[j].centroid[0]
        dy = old[i].centroid[1] - new[j].centroid[1]
        pairs.append(MatchPair(old=old[i], new=new[j], distance=(dx * dx + dy * dy) ** 0.5))

    pairs += [MatchPair(old=e, new=None) for i, e in enumerate(old) if i not in used_old]
    pairs += [MatchPair(old=None, new=e) for j, e in enumerate(new) if j not in used_new]
    return pairs
