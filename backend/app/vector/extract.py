"""Extract vector primitives and text spans from a native-vector PDF page.

Coordinates are normalized to [0,1] against the page rect immediately so
every later stage is resolution/page-size independent.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import fitz

Point = tuple[float, float]


@dataclass
class Primitive:
    kind: str  # "l" line, "c" bezier curve, "re" rect, "qu" quad
    points: list[Point]  # normalized endpoints/control points
    width: float = 0.0

    @property
    def endpoints(self) -> list[Point]:
        """Points used for connectivity clustering (first and last)."""
        if not self.points:
            return []
        return [self.points[0], self.points[-1]]


@dataclass
class RawTextSpan:
    text: str
    bbox: tuple[float, float, float, float]  # normalized
    size: float = 0.0
    confidence: float = 1.0


def _norm_point(p, w: float, h: float) -> Point:
    return (p.x / w, p.y / h)


def _norm_rect(r: fitz.Rect, w: float, h: float) -> tuple[float, float, float, float]:
    return (r.x0 / w, r.y0 / h, r.x1 / w, r.y1 / h)


def extract_primitives(page: fitz.Page) -> list[Primitive]:
    w, h = page.rect.width, page.rect.height
    primitives: list[Primitive] = []
    for drawing in page.get_drawings():
        width = drawing.get("width") or 0.0
        for item in drawing["items"]:
            op = item[0]
            if op == "l":  # line: (op, p1, p2)
                pts = [_norm_point(item[1], w, h), _norm_point(item[2], w, h)]
            elif op == "c":  # bezier: (op, p1, p2, p3, p4)
                pts = [_norm_point(p, w, h) for p in item[1:5]]
            elif op == "re":  # rect: (op, rect, orientation?)
                r = item[1]
                pts = [
                    (r.x0 / w, r.y0 / h),
                    (r.x1 / w, r.y0 / h),
                    (r.x1 / w, r.y1 / h),
                    (r.x0 / w, r.y1 / h),
                ]
            elif op == "qu":  # quad: (op, quad)
                q = item[1]
                pts = [_norm_point(p, w, h) for p in (q.ul, q.ur, q.lr, q.ll)]
            else:
                continue
            primitives.append(Primitive(kind=op, points=pts, width=width))
    return primitives


def extract_text_spans(page: fitz.Page) -> list[RawTextSpan]:
    w, h = page.rect.width, page.rect.height
    spans: list[RawTextSpan] = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text:
                    continue
                spans.append(
                    RawTextSpan(
                        text=text,
                        bbox=_norm_rect(fitz.Rect(span["bbox"]), w, h),
                        size=span.get("size", 0.0),
                    )
                )
    return spans
