"""Map a normalized centroid to a human location label via a 3x3 grid."""
from __future__ import annotations


def bucket_location(cx: float, cy: float) -> str:
    col = "left" if cx < 1 / 3 else ("right" if cx > 2 / 3 else "center")
    row = "upper" if cy < 1 / 3 else ("lower" if cy > 2 / 3 else "middle")

    if row == "middle" and col == "center":
        return "center"
    if row == "middle":
        return col  # "left" / "right" (middle band)
    if col == "center":
        return row  # "upper" / "lower" (middle column)
    return f"{row}-{col}"  # e.g. "lower-right"
