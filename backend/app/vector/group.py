"""Group vector primitives into entities via connectivity clustering.

Two primitives belong to the same entity when any endpoint of one lies
within a small tolerance of an endpoint of the other (union-find over a
spatial grid). This approximates "one drawn symbol/feature" without a
trained model — GAT-CADNet-style learned symbol spotting is the documented
future upgrade path.
"""
from __future__ import annotations

import uuid
from collections import Counter, defaultdict

from ..config import settings
from ..models.diff_result import Entity, EntityKind
from .extract import Primitive, RawTextSpan


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def group_into_entities(
    primitives: list[Primitive], tol: float | None = None
) -> list[Entity]:
    if not primitives:
        return []
    tol = tol if tol is not None else settings.endpoint_join_tol

    uf = _UnionFind(len(primitives))
    # spatial grid over endpoints: cell size = tol, check own + neighbor cells
    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    cell = max(tol, 1e-6)

    for idx, prim in enumerate(primitives):
        for (x, y) in prim.endpoints:
            cx, cy = int(x / cell), int(y / cell)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for other in grid.get((cx + dx, cy + dy), []):
                        if other == idx:
                            continue
                        for (ox, oy) in primitives[other].endpoints:
                            if abs(ox - x) <= tol and abs(oy - y) <= tol:
                                uf.union(idx, other)
                                break
            grid[(cx, cy)].append(idx)

    clusters: dict[int, list[Primitive]] = defaultdict(list)
    for idx, prim in enumerate(primitives):
        clusters[uf.find(idx)].append(prim)

    entities: list[Entity] = []
    for prims in clusters.values():
        xs = [x for p in prims for (x, _) in p.points]
        ys = [y for p in prims for (_, y) in p.points]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        centroid = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
        signature = dict(Counter(p.kind for p in prims))
        entities.append(
            Entity(
                id=uuid.uuid4().hex[:12],
                kind=EntityKind.GEOMETRY,
                bbox=bbox,
                centroid=centroid,
                shape_signature=signature,
                primitive_count=len(prims),
            )
        )
    return entities


def text_spans_to_entities(spans: list[RawTextSpan]) -> list[Entity]:
    entities: list[Entity] = []
    for span in spans:
        x0, y0, x1, y1 = span.bbox
        entities.append(
            Entity(
                id=uuid.uuid4().hex[:12],
                kind=EntityKind.TEXT,
                bbox=span.bbox,
                centroid=((x0 + x1) / 2, (y0 + y1) / 2),
                text=span.text,
                confidence=span.confidence,
            )
        )
    return entities
