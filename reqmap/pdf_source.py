"""PDF to markdown, delegated to the pdf2md submodule.

pdf2md lives in ``pdf2md/`` (git submodule, package under ``pdf2md/src``).
"""

import re
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Optional

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PDF2MD_SRC = _PROJECT_ROOT / "pdf2md" / "src"
if str(_PDF2MD_SRC) not in sys.path:
    sys.path.insert(0, str(_PDF2MD_SRC))

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


def apply_post_process(
    markdown: str, post_process: Mapping[str, str], source: Path, assets_dir: Optional[Path] = None
) -> str:
    """Run pdf2md post-processing plugins (``--post-process NAME``) on ``markdown``.

    ``post_process`` maps a plugin name to its script, relative to the repository root; the
    plugins run in the order given. They are registered in a throwaway plugin folder through
    pdf2md's own API, so the user's registry is neither read nor modified.
    """
    from pdf2md.plugins import load_plugins, post_process_outputs, register_plugin

    with tempfile.TemporaryDirectory(prefix="pdf2md_plugins_") as tmp:
        plugin_dir = Path(tmp) / "plugins"
        for name, script in post_process.items():
            path = (_PROJECT_ROOT / script).resolve()
            if not path.is_relative_to(_PROJECT_ROOT):
                raise ValueError(f"plugin script outside the repository: {script}")
            register_plugin(name, path, plugin_dir)
        md_path = Path(tmp) / "document.md"
        md_path.write_text(markdown, encoding="utf-8")
        post_process_outputs(
            load_plugins(list(post_process), plugin_dir), Path(source), md_path, None,
            assets_dir or Path(tmp),
        )
        return md_path.read_text(encoding="utf-8")


def pdf_to_markdown(
    pdf_path: Path,
    req_id_pattern: Optional[str] = None,
    enable_ocr: bool = True,
    images_dir: Optional[Path] = None,
    asset_url_prefix: Optional[str] = None,
    tables_as_images: Optional[int] = None,
    post_process: Optional[Mapping[str, str]] = None,
) -> str:
    """Convert a PDF to markdown with pdf2md, ready for ``parse_nodes``.

    With ``images_dir`` the extracted figures are kept there and referenced under
    ``asset_url_prefix``; without it they live in a temporary directory and are dropped.
    ``tables_as_images`` (pdf2md ``--tables-as-images``) renders the tables of at least that
    many rows as pictures of their page area instead of Markdown text; it needs ``images_dir``
    to be kept, otherwise those tables would vanish with the temporary directory.
    ``post_process`` is applied to pdf2md's markdown before the images are post-processed
    (see :func:`apply_post_process`).
    """
    if tables_as_images is not None and images_dir is None:
        raise ValueError("tables_as_images needs images_dir")
    from pdf2md.models import Settings
    from pdf2md.pipeline import convert_pdf

    settings = Settings(ocr_enabled=enable_ocr, tables_as_images=tables_as_images)
    # Figures must always be extracted: ID pictures only become text through their alt text.
    if images_dir is None:
        with tempfile.TemporaryDirectory(prefix="pdf2md_") as tmp:
            result = convert_pdf(Path(pdf_path), settings, images_dir=Path(tmp))
        markdown = _plugins(result.markdown, post_process, pdf_path, None)
        return inline_id_images(markdown, req_id_pattern)
    images_dir.mkdir(parents=True, exist_ok=True)
    result = convert_pdf(Path(pdf_path), settings, images_dir=images_dir)
    markdown = _plugins(result.markdown, post_process, pdf_path, images_dir)
    return inline_id_images(markdown, req_id_pattern, images_dir, asset_url_prefix)


def _plugins(
    markdown: str, post_process: Optional[Mapping[str, str]], source: Path, assets_dir: Optional[Path]
) -> str:
    return apply_post_process(markdown, post_process, source, assets_dir) if post_process else markdown
