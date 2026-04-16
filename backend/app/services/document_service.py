"""Document upload and file management service."""

import logging
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}


def validate_upload(file: UploadFile) -> None:
    """Raise ValueError for invalid uploads."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")


async def save_upload(file: UploadFile) -> tuple[str, str]:
    """Persist the uploaded file and return (unique_filename, absolute_path)."""
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "upload").suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    dest = settings.upload_dir / unique_name

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise ValueError(
            f"File too large ({len(content):,} bytes). Max: {settings.max_upload_bytes:,} bytes"
        )

    dest.write_bytes(content)
    logger.info("Saved upload %s → %s (%d bytes)", file.filename, dest, len(content))
    return unique_name, str(dest)
