"""Rule-based natural-language change summary (FR-6).

Pure string templating over computed stats — no LLM anywhere. Mirrors the
example paragraph style from the requirements document.
"""
from __future__ import annotations

from ..config import settings
from ..models.diff_result import DiffResult
from ..models.schemas import RegionStat, StatsSummary
from .severity import bucket_severity

_NUM_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
}


def _num_word(n: int) -> str:
    return _NUM_WORDS.get(n, str(n))


def _describe(stat: RegionStat) -> str:
    what = "annotation" if stat.kind == "text" else "drawing element"
    loc = stat.location if stat.location == "center" else f"{stat.location} region"
    if stat.change_type == "added":
        return f"a new {what} has appeared in the {loc}"
    if stat.change_type == "removed":
        return f"an existing {what} in the {loc} has been removed"
    if stat.change_type == "moved":
        return f"a {what} near the {loc} has shifted position"
    # modified
    if stat.detail and stat.kind == "text":
        return f"an annotation in the {loc} was changed ({stat.detail})"
    return f"structural modifications were detected near the {loc}"


def generate_summary(diff: DiffResult, stats: StatsSummary) -> str:
    if stats.total_regions == 0:
        base = "No significant differences were detected between the two drawings."
        if diff.compare_mode == "text-only":
            base += (
                " Note: at least one input contained no vector data, so only "
                "text and annotation changes could be evaluated."
            )
        return base

    severity = bucket_severity(stats.total_changed_area_fraction)
    n = stats.total_regions
    parts = [
        f"The comparison identified {_num_word(n)} "
        f"{severity} change{'s' if n != 1 else ''} between the two drawings."
    ]

    top = stats.per_region[: settings.max_summary_regions]
    if top:
        sentences = [_describe(s) for s in top]
        if len(sentences) == 1:
            body = sentences[0].capitalize() + "."
        else:
            body = (
                sentences[0].capitalize()
                + ", while "
                + "; additionally, ".join(sentences[1:])
                + "."
            )
        parts.append(body)

    remaining = n - len(top)
    if remaining > 0:
        parts.append(
            f"{_num_word(remaining).capitalize()} further smaller "
            f"change{'s were' if remaining != 1 else ' was'} also detected."
        )

    parts.append(
        "These changes affect approximately "
        f"{stats.total_changed_area_fraction * 100:.1f}% of the total drawing area."
    )

    if diff.compare_mode == "text-only":
        parts.append(
            "Note: at least one input contained no vector data, so this "
            "comparison covers text and annotations only (detected via OCR); "
            "pure geometry changes are not evaluated for raster inputs."
        )

    return " ".join(parts)
