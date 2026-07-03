"""Upload validation: extension, size, and magic-byte checks (FR-1)."""
from __future__ import annotations

from pathlib import Path

from ..config import settings

# magic bytes for the formats we accept
_MAGIC = {
    ".pdf": [b"%PDF"],
    ".png": [b"\x89PNG"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
}


class ValidationError(ValueError):
    pass


def validate_upload(filename: str, data: bytes) -> str:
    """Validate an uploaded file. Returns the normalized extension.

    Raises ValidationError with a user-facing message on failure.
    """
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.allowed_extensions)}"
        )
    if not data:
        raise ValidationError(f"File '{filename}' is empty.")
    if len(data) > settings.max_file_size_mb * 1024 * 1024:
        raise ValidationError(
            f"File '{filename}' exceeds the {settings.max_file_size_mb} MB size limit."
        )
    if not any(data.startswith(m) for m in _MAGIC[ext]):
        raise ValidationError(
            f"File '{filename}' does not look like a valid {ext} file (bad file header)."
        )
    return ext
