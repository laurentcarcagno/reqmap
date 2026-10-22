"""Tests for the pdf2md image post-processing."""

from pathlib import Path

from reqmap.pdf_source import inline_id_images

ID_PATTERN = r"^(HAR\s+SSOW-\d+)\s*/\s*(.+)$"
MARKDOWN = "\n".join([
    "Intro",
    "![HAR SSOW-2 / Input-events](out/p0015_02.png)",
    "![Figure 1: Layout](out/p0015_03.png)",
    "![Gone](out/missing.png)",
    "Outro",
])


def test_id_pictures_become_text_and_figures_are_dropped_without_a_store():
    assert inline_id_images(MARKDOWN, ID_PATTERN) == "Intro\nHAR SSOW-2 / Input-events\nOutro"


def test_figures_are_kept_when_stored(tmp_path: Path):
    (tmp_path / "p0015_03.png").write_bytes(b"png")
    result = inline_id_images(MARKDOWN, ID_PATTERN, tmp_path, "/api/v1/documents/d/assets")
    assert result.splitlines() == [
        "Intro",
        "HAR SSOW-2 / Input-events",
        "![Figure 1: Layout](/api/v1/documents/d/assets/p0015_03.png)",
        "Outro",
    ]


def _pdf_with_a_table(path: Path) -> None:
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 80), "1 Scope", fontsize=16)
    page.insert_text((72, 110), "Some body text before the table.", fontsize=10)
    left, top, cell_w, cell_h = 72, 140, 110, 24
    for row in range(4):
        for col in range(3):
            rect = pymupdf.Rect(left + col * cell_w, top + row * cell_h,
                                left + (col + 1) * cell_w, top + (row + 1) * cell_h)
            page.draw_rect(rect, width=0.8)
            page.insert_text((rect.x0 + 4, rect.y0 + 16), f"r{row}c{col}", fontsize=10)
    doc.save(path)


def test_tables_as_images_keeps_the_table_as_a_stored_picture(tmp_path: Path):
    from reqmap.pdf_source import pdf_to_markdown

    pdf = tmp_path / "doc.pdf"
    _pdf_with_a_table(pdf)
    images = tmp_path / "assets"
    as_text = pdf_to_markdown(pdf, enable_ocr=False)
    as_images = pdf_to_markdown(pdf, enable_ocr=False, images_dir=images,
                                asset_url_prefix="/assets", tables_as_images=1)
    assert "| r0c0" in as_text or "r0c0" in as_text
    assert "| ---" not in as_images
    assert "![Table (page 1)](/assets/p0001_t01.png)" in as_images
    assert (images / "p0001_t01.png").is_file()


def test_tables_as_images_needs_a_kept_images_dir(tmp_path: Path):
    import pytest

    from reqmap.pdf_source import pdf_to_markdown

    with pytest.raises(ValueError, match="images_dir"):
        pdf_to_markdown(tmp_path / "doc.pdf", tables_as_images=1)
