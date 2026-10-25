"""PDF to markdown, delegated to the pdf2md server (see :mod:`reqmap.pdf2md_client`)."""

import re
from pathlib import Path
from typing import Mapping, Optional

from reqmap.pdf2md_client import Pdf2mdServer, convert

_IMAGE_LINE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]*)\)\s*$")


def inline_id_images(
    markdown: str,
    req_id_pattern: Optional[str],
    images_dir: Optional[Path] = None,
    asset_url_prefix: Optional[str] = None,
) -> str:
    """Post-process the pdf2md image lines.

    Requirement IDs drawn as pictures are OCR'd by pdf2md into the image alt text: those
    lines become plain text. Other figures are kept as ``![alt](<asset_url_prefix>/<file>)``
    when ``images_dir`` and ``asset_url_prefix`` say where they are served from, and dropped
    otherwise so their captions do not leak into node descriptions.
    """
    id_re = re.compile(req_id_pattern, re.IGNORECASE) if req_id_pattern else None
    lines = []
    for line in markdown.splitlines():
        match = _IMAGE_LINE_RE.match(line)
        if match is None:
            lines.append(line)
            continue
        alt, target = match.group(1).strip(), match.group(2)
        if id_re and id_re.match(alt):
            lines.append(alt)
        elif images_dir and asset_url_prefix:
            name = Path(target).name
            if (images_dir / name).is_file():
                lines.append(f"![{alt}]({asset_url_prefix}/{name})")
    return "\n".join(lines)


def pdf_to_markdown(
    pdf_path: Path,
    req_id_pattern: Optional[str] = None,
    enable_ocr: bool = True,
    images_dir: Optional[Path] = None,
    asset_url_prefix: Optional[str] = None,
    tables_as_images: Optional[int] = None,
    tables_html: bool = False,
    post_process: Optional[Mapping[str, str]] = None,
    server: Optional[Pdf2mdServer] = None,
) -> str:
    """Convert a PDF to markdown on the pdf2md server, ready for ``parse_nodes``.

    With ``images_dir`` the extracted figures are kept there and referenced under
    ``asset_url_prefix``; without it they are dropped.
    ``tables_as_images`` (pdf2md ``--tables-as-images``) renders the tables of at least that
    many rows as pictures of their page area instead of Markdown text; it needs ``images_dir``
    to be kept, otherwise those tables would vanish.
    ``tables_html`` (pdf2md ``--tables-html``) inserts them as HTML keeping colours and text styles;
    it excludes ``tables_as_images``.
    ``post_process`` maps the names of pdf2md post-processing plugins to their script (relative to
    the repository root); the server runs them, in that order, on its Markdown.
    ``server`` defaults to the one of the PDF2MD_* environment variables.
    """
    if tables_as_images is not None and images_dir is None:
        raise ValueError("tables_as_images needs images_dir")
    if tables_html and tables_as_images is not None:
        raise ValueError("tables_html and tables_as_images are mutually exclusive")
    markdown, files = convert(
        server or Pdf2mdServer.from_env(),
        Path(pdf_path),
        ocr=enable_ocr,
        tables="html" if tables_html else "images" if tables_as_images is not None else "markdown",
        tables_min_rows=tables_as_images or 1,
        post_process=post_process,
    )
    if images_dir is None:
        return inline_id_images(markdown, req_id_pattern)
    images_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        if name in markdown:  # figures the Markdown refers to
            (images_dir / name).write_bytes(content)
    return inline_id_images(markdown, req_id_pattern, images_dir, asset_url_prefix)
