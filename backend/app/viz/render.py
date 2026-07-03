"""Visualization rendering (FR-4).

Pages are rasterized here purely for human display — the diff itself was
already decided on structured entities before any pixel exists. Boxes are
drawn with Pillow on the rendered page.
"""
from __future__ import annotations

import io

import fitz
from PIL import Image, ImageDraw, ImageFont

from ..config import settings
from ..models.diff_result import ChangeType, DiffResult, Region

_COLORS = {
    ChangeType.ADDED: (46, 160, 67),      # green
    ChangeType.REMOVED: (218, 54, 51),    # red
    ChangeType.MOVED: (227, 179, 65),     # amber
    ChangeType.MODIFIED: (31, 111, 235),  # blue
}


def render_page(page: fitz.Page, dpi: int | None = None) -> Image.Image:
    pix = page.get_pixmap(dpi=dpi or settings.render_dpi)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def _draw_regions(img: Image.Image, regions: list[Region], use_old_bbox: bool) -> Image.Image:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    try:
        font = ImageFont.truetype("arial.ttf", max(12, h // 90))
    except OSError:
        font = ImageFont.load_default()

    for region in regions:
        bbox = region.old_bbox if (use_old_bbox and region.old_bbox) else region.bbox
        if use_old_bbox and region.change_type == ChangeType.ADDED:
            continue  # additions don't exist on the old page
        if not use_old_bbox and region.change_type == ChangeType.REMOVED:
            bbox = region.bbox  # removals drawn where the element used to be
        color = _COLORS[region.change_type]
        px = [bbox[0] * w, bbox[1] * h, bbox[2] * w, bbox[3] * h]
        # pad tiny boxes so they stay visible
        pad = max(2.0, 0.002 * max(w, h))
        px = [px[0] - pad, px[1] - pad, px[2] + pad, px[3] + pad]
        draw.rectangle(px, outline=color, width=max(2, h // 400))
        tag = region.change_type.value
        draw.text((px[0], max(0, px[1] - font.size - 2)), tag, fill=color, font=font)
    return img


def render_bbox_overlay(page_b: fitz.Page, diff: DiffResult) -> bytes:
    """New version annotated with all change regions."""
    img = _draw_regions(render_page(page_b), diff.regions, use_old_bbox=False)
    return _to_png(img)


def render_side_by_side(page_a: fitz.Page, page_b: fitz.Page, diff: DiffResult) -> bytes:
    img_a = _draw_regions(render_page(page_a), diff.regions, use_old_bbox=True)
    img_b = _draw_regions(render_page(page_b), diff.regions, use_old_bbox=False)
    # equalize heights
    target_h = max(img_a.height, img_b.height)
    def _scale(im: Image.Image) -> Image.Image:
        if im.height == target_h:
            return im
        w = round(im.width * target_h / im.height)
        return im.resize((w, target_h))
    img_a, img_b = _scale(img_a), _scale(img_b)
    gap = 16
    combo = Image.new("RGB", (img_a.width + gap + img_b.width, target_h), (255, 255, 255))
    combo.paste(img_a, (0, 0))
    combo.paste(img_b, (img_a.width + gap, 0))
    return _to_png(combo)


def render_original(page: fitz.Page) -> bytes:
    return _to_png(render_page(page))


def _to_png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
