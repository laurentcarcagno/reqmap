"""PDF to markdown, delegated to the pdf2md submodule.

pdf2md lives in ``pdf2md/`` (git submodule, package under ``pdf2md/src``).
"""

import re
import sys
import tempfile
from pathlib import Path
from typing import Optional

_PDF2MD_SRC = Path(__file__).resolve().parents[1] / "pdf2md" / "src"
if str(_PDF2MD_SRC) not in sys.path:
    sys.path.insert(0, str(_PDF2MD_SRC))

_IMAGE_LINE_RE = re.compile(r"^!\[([^\]]*)\]\([^)]*\)\s*$")


def inline_id_images(markdown: str, req_id_pattern: Optional[str]) -> str:
    """Replace pdf2md image lines by their alt text when it is a requirement ID line.

    Requirement IDs drawn as pictures are OCR'd by pdf2md into the image alt text.
    Other figures are dropped so their captions do not leak into node descriptions.
    """
    id_re = re.compile(req_id_pattern, re.IGNORECASE) if req_id_pattern else None
    lines = []
    for line in markdown.splitlines():
        match = _IMAGE_LINE_RE.match(line)
        if match is None:
            lines.append(line)
        elif id_re and id_re.match(match.group(1).strip()):
            lines.append(match.group(1).strip())
    return "\n".join(lines)


def pdf_to_markdown(
    pdf_path: Path, req_id_pattern: Optional[str] = None, enable_ocr: bool = True
) -> str:
    """Convert a PDF to markdown with pdf2md, ready for ``parse_nodes``."""
    from pdf2md.models import Settings
    from pdf2md.pipeline import convert_pdf

    # Figures must be extracted: ID pictures only become text through their alt text.
    with tempfile.TemporaryDirectory(prefix="pdf2md_") as images_dir:
        result = convert_pdf(
            Path(pdf_path), Settings(ocr_enabled=enable_ocr), images_dir=Path(images_dir)
        )
    return inline_id_images(result.markdown, req_id_pattern)
