"""PDF text extraction to markdown.

Uses pymupdf4llm (primary) with plain PyMuPDF fallback.
Includes table detection via both line-based and span-clustering methods.
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False

from reqmap.inline_image_ocr import InlineImageOCR, RAPIDOCR_AVAILABLE
from reqmap.header_footer_detector import HeaderFooterDetector
from reqmap.markdown_cleaner import MarkdownCleaner


class PDFExtractor:
    """Extract markdown from PDF documents.

    Pipeline:
    1. Extract raw markdown via pymupdf4llm (or plain PyMuPDF fallback).
    2. Detect and remove repeating headers/footers.
    3. OCR inline text-images (requirement IDs embedded as raster images).
    4. Clean markdown (TOC removal, heading inference, table repair, etc.).
    """

    def __init__(self, *, enable_ocr: bool = True,
                 cleaning_config: dict = None,
                 hf_threshold_pages: int = 3,
                 hf_zone_pct: float = 0.10):
        """
        Args:
            enable_ocr: Whether to run InlineImageOCR on detected text-images.
            cleaning_config: Dict of cleaning options passed to MarkdownCleaner.
            hf_threshold_pages: Minimum pages for header/footer detection.
            hf_zone_pct: Top/bottom zone fraction for header/footer detection.
        """
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF (fitz) is required. Install with: pip install pymupdf")

        self._inline_ocr: Optional[InlineImageOCR] = None
        if enable_ocr and RAPIDOCR_AVAILABLE:
            try:
                self._inline_ocr = InlineImageOCR()
                logger.info("InlineImageOCR enabled")
            except Exception as e:
                logger.warning(f"InlineImageOCR not available: {e}")

        self._cleaner = MarkdownCleaner(cleaning_config or {})
        self._hf_threshold = hf_threshold_pages
        self._hf_zone_pct = hf_zone_pct

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, pdf_path: Path) -> Tuple[str, str]:
        """Extract raw and clean markdown from a PDF.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Tuple of (raw_markdown, clean_markdown).
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Step 1 — extract raw markdown
        raw_text, pages_data = self._extract_markdown(pdf_path)
        logger.info(f"Extracted {len(raw_text)} chars from {pdf_path.name}")

        # Step 2 — remove headers / footers
        raw_text = self._remove_headers_footers(pdf_path, raw_text, pages_data)

        # Step 3 — OCR inline text-images
        if self._inline_ocr:
            raw_text = self._ocr_inline_images(pdf_path, raw_text)

        # Step 4 — clean markdown
        cleaning_result = self._cleaner.clean(raw_text)
        clean_text = cleaning_result.cleaned_text
        logger.info(
            f"Cleaned: {cleaning_result.stats.get('headings_inferred', 0)} headings inferred, "
            f"{len(cleaning_result.removed_sections)} sections removed, "
            f"{cleaning_result.stats.get('lines_reduction_pct', 0)}% reduction"
        )

        return raw_text, clean_text

    # ------------------------------------------------------------------
    # Extraction backends
    # ------------------------------------------------------------------

    def _extract_markdown(self, pdf_path: Path) -> Tuple[str, Optional[List[tuple]]]:
        """Try pymupdf4llm first, then fall back to plain PyMuPDF."""

        # --- pymupdf4llm path ---
        if PYMUPDF4LLM_AVAILABLE:
            try:
                md_text = pymupdf4llm.to_markdown(
                    str(pdf_path),
                    write_images=False,
                    table_strategy="lines",
                    show_progress=False,
                    force_text=True,
                )
                if not md_text or not md_text.strip():
                    raise ValueError("pymupdf4llm returned empty text")

                md_text = self._sanitize(md_text)

                # Build pages_data for header/footer detection
                pages_data = self._pages_data(pdf_path)

                logger.info(f"pymupdf4llm: {len(md_text)} chars from {pdf_path.name}")
                return md_text, pages_data

            except Exception as e:
                logger.warning(f"pymupdf4llm failed, falling back to plain PyMuPDF: {e}")

        # --- Plain PyMuPDF fallback ---
        pages_data: List[tuple] = []
        doc = fitz.open(str(pdf_path))
        if doc.page_count == 0:
            doc.close()
            raise ValueError("PDF has no pages")

        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                page_text = self._build_page_text(page)
                if page_text and page_text.strip():
                    page_text = self._sanitize(page_text)
                else:
                    page_text = ""
                if page_text:
                    pages_data.append((page_num + 1, page_text))
            except Exception as e:
                logger.warning(f"Page {page_num + 1}: {e}")

        doc.close()

        if not pages_data:
            raise ValueError("No text found in PDF (possibly scanned or protected)")

        full_text = "\n".join([text for _, text in pages_data])
        return full_text, pages_data

    # ------------------------------------------------------------------
    # Header / footer removal
    # ------------------------------------------------------------------

    def _remove_headers_footers(self, pdf_path: Path, raw_text: str,
                                pages_data: Optional[List[tuple]]) -> str:
        """Detect and strip repeating headers/footers."""
        try:
            detector = HeaderFooterDetector()
            detector.detect(
                str(pdf_path),
                threshold_pages=self._hf_threshold,
                top_bottom_pct=self._hf_zone_pct,
            )

            header_pat, footer_pat = detector.get_text_patterns()
            if header_pat:
                raw_text = self._cleaner.remove_pattern_from_text(raw_text, header_pat)
                logger.info(f"Removed header pattern: {header_pat[:50]}...")
            if footer_pat:
                raw_text = self._cleaner.remove_pattern_from_text(raw_text, footer_pat)
                logger.info(f"Removed footer pattern: {footer_pat[:50]}...")

            header_images, footer_images = detector.get_image_patterns()
            if header_images or footer_images:
                raw_text = self._cleaner.remove_header_footer_images(
                    raw_text, header_images, footer_images
                )
        except Exception as e:
            logger.warning(f"Header/footer detection failed: {e}")
            # Fallback: text-based detection
            if pages_data and len(pages_data) >= 3:
                page_texts = [pt for _, pt in pages_data]
                header_pat, footer_pat = self._cleaner.detect_repeated_content(
                    page_texts, min_occurrences=3
                )
                if header_pat:
                    raw_text = self._cleaner.remove_pattern_from_text(raw_text, header_pat)
                if footer_pat:
                    raw_text = self._cleaner.remove_pattern_from_text(raw_text, footer_pat)

        return raw_text

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------

    def _ocr_inline_images(self, pdf_path: Path, markdown: str) -> str:
        """OCR inline text-images and inject/replace into markdown."""
        logger.info(f"InlineImageOCR: starting for {pdf_path.name}")
        try:
            items = self._inline_ocr.extract_inline_texts(pdf_path)
            logger.info(f"InlineImageOCR: {len(items)} items found")
            if items:
                markdown = self._inline_ocr.inject_into_markdown(markdown, items)
        except Exception as e:
            logger.warning(f"InlineImageOCR failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        return markdown

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize(text: str) -> str:
        """Remove null bytes and normalize line endings."""
        text = text.replace('\x00', '')
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text

    @staticmethod
    def _pages_data(pdf_path: Path) -> List[tuple]:
        """Build (page_num, page_text) list from plain PyMuPDF."""
        pages = []
        try:
            doc = fitz.open(str(pdf_path))
            for pn in range(doc.page_count):
                try:
                    pt = doc[pn].get_text()
                    if pt and pt.strip():
                        pages.append((pn + 1, pt))
                except Exception:
                    pass
            doc.close()
        except Exception:
            pass
        return pages

    # ------------------------------------------------------------------
    # Table-aware page text (plain PyMuPDF fallback)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_page_text(page, header_zone_pct: float = 0.10) -> str:
        """Build page text with tables embedded at their correct positions.

        Collects table regions, iterates text blocks in y-order, skips blocks
        covered by tables, and interleaves table markdown.
        """
        table_regions: list = []
        line_bboxes: list = []
        h = page.rect.height
        threshold = h * header_zone_pct

        # Detector 1: span-clustering
        cluster = PDFExtractor._cluster_spans_to_tables(page, header_zone_pct)
        for cy0, cy1, cmd in cluster:
            cb = (0, cy0, page.rect.width, cy1)
            table_regions.append((cy0, cy1, cmd))
            line_bboxes.append(cb)

        # Detector 2: line/border-based find_tables()
        try:
            tf = page.find_tables()
            for tab in tf.tables:
                if tab.bbox[1] <= threshold:
                    continue
                if any(PDFExtractor._bbox_overlaps(tab.bbox, lb) for lb in line_bboxes):
                    continue
                try:
                    cells = tab.extract()
                except Exception:
                    continue
                if not cells or len(cells) < 2:
                    continue

                def _norm(val):
                    if val is None:
                        return ''
                    text = str(val).strip()
                    text = re.sub(r'<br\s*/?>', ' ', text, flags=re.IGNORECASE)
                    return text.replace('\n', ' ').strip()

                md_rows = []
                for i, row in enumerate(cells):
                    row_cells = [_norm(c) for c in row]
                    md_rows.append('| ' + ' | '.join(row_cells) + ' |')
                    if i == 0:
                        md_rows.append('| ' + ' | '.join(['---'] * len(row_cells)) + ' |')

                y0, y1 = tab.bbox[1], tab.bbox[3]
                table_regions.append((y0, y1, '\n'.join(md_rows)))
                line_bboxes.append(tab.bbox)
        except Exception:
            pass

        if not table_regions:
            return page.get_text()

        table_regions.sort(key=lambda t: t[0])

        # Collect text lines not covered by tables
        items: list = []
        d = page.get_text("dict")
        for blk in d.get("blocks", []):
            if blk.get("type") != 0:
                continue
            for ln in blk.get("lines", []):
                ly0 = ln["bbox"][1]
                ly1 = ln["bbox"][3]
                ly_mid = (ly0 + ly1) / 2
                covered = any(ty0 - 2 <= ly_mid <= ty1 + 2
                              for ty0, ty1, _ in table_regions)
                if covered:
                    continue
                line_text = " ".join(
                    sp.get("text", "") for sp in ln.get("spans", [])
                ).strip()
                if line_text:
                    items.append((ly0, line_text))

        for ty0, _ty1, tmd in table_regions:
            items.append((ty0, tmd))

        items.sort(key=lambda x: x[0])
        return "\n\n".join(content for _, content in items)

    @staticmethod
    def _bbox_overlaps(b1: tuple, b2: tuple, tolerance: float = 15.0) -> bool:
        """Return True if two bboxes overlap within tolerance."""
        return (
            b1[0] < b2[2] + tolerance and b2[0] < b1[2] + tolerance
            and b1[1] < b2[3] + tolerance and b2[1] < b1[3] + tolerance
        )

    @staticmethod
    def _cluster_spans_to_tables(page, header_zone_pct: float = 0.10) -> list:
        """Detect whitespace-layout tables via span x-position clustering.

        Returns list of (y0, y1, markdown_str) tuples.
        """
        if not PYMUPDF_AVAILABLE:
            return []

        results = []
        try:
            page_w = page.rect.width
            page_h = page.rect.height
            y_min_content = page_h * header_zone_pct
            col_tol = max(8.0, page_w * 0.012)

            # Phase 1: extract spans below header zone
            d = page.get_text("dict")
            spans = []
            for block in d.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        txt = span.get("text", "").strip()
                        if not txt:
                            continue
                        if span["bbox"][1] < y_min_content:
                            continue
                        spans.append(span)

            if len(spans) < 6:
                return []

            # Phase 2: median fontsize → row gap threshold
            sizes = sorted(s["size"] for s in spans if s.get("size", 0) > 0)
            median_sz = sizes[len(sizes) // 2] if sizes else 10.0
            row_gap = median_sz * 0.8

            # Phase 3: group spans into visual rows by y-band
            spans_sorted = sorted(spans, key=lambda s: s["bbox"][1])
            rows = []
            row_y0s = []

            cur_row: list = []
            cur_y = None
            for sp in spans_sorted:
                y = sp["bbox"][1]
                if cur_y is None or (y - cur_y) > row_gap:
                    if cur_row:
                        rows.append(cur_row)
                        row_y0s.append(cur_row[0]["bbox"][1])
                    cur_row = [sp]
                    cur_y = y
                else:
                    cur_row.append(sp)
            if cur_row:
                rows.append(cur_row)
                row_y0s.append(cur_row[0]["bbox"][1])

            if len(rows) < 3:
                return []

            # Phase 4: classify each row by column count
            def _distinct_cols(row_spans: list) -> int:
                if not row_spans:
                    return 0
                srt = sorted(row_spans, key=lambda s: s["bbox"][0])
                groups = 1
                grp_right = srt[0]["bbox"][2]
                for sp in srt[1:]:
                    left = sp["bbox"][0]
                    if left - grp_right >= col_tol:
                        groups += 1
                    grp_right = max(grp_right, sp["bbox"][2])
                return groups

            row_ncols = [_distinct_cols(r) for r in rows]

            _SEC_NUM_RE = re.compile(r'^\d+(\.\d+)*$')

            def _is_section_heading_row(row_spans: list) -> bool:
                if not row_spans:
                    return False
                leftmost = min(row_spans, key=lambda s: s["bbox"][0])
                txt = leftmost.get("text", "").strip()
                x0 = leftmost["bbox"][0]
                return x0 < page_w * 0.12 and bool(_SEC_NUM_RE.match(txt))

            multi_idxs = [
                i for i, n in enumerate(row_ncols)
                if n >= 2 and not _is_section_heading_row(rows[i])
            ]

            if not multi_idxs:
                return []

            # Phase 5: group consecutive multi-column indices into regions
            max_y_gap = median_sz * 4.0
            regions: list = []
            seg_start = multi_idxs[0]
            seg_end = multi_idxs[0]

            for idx in multi_idxs[1:]:
                y_dist = row_y0s[idx] - row_y0s[seg_end]
                if y_dist <= max_y_gap:
                    seg_end = idx
                else:
                    regions.append((seg_start, seg_end))
                    seg_start = idx
                    seg_end = idx
            regions.append((seg_start, seg_end))

            # Phase 6: process each table region
            for reg_start, reg_end in regions:
                ext_end = reg_end
                while ext_end + 1 < len(rows):
                    if row_y0s[ext_end + 1] - row_y0s[ext_end] > max_y_gap / 2:
                        break
                    if row_ncols[ext_end + 1] >= 2:
                        break
                    ext_end += 1

                region_rows = rows[reg_start: ext_end + 1]
                region_y0s = row_y0s[reg_start: ext_end + 1]
                anchor_rows = rows[reg_start: reg_end + 1]

                if len(region_rows) < 2:
                    continue

                # Cluster x0 values
                local_x0s = sorted(
                    s["bbox"][0] for row in region_rows for s in row
                )
                raw_buckets: list = []
                if local_x0s:
                    g = [local_x0s[0]]
                    for x in local_x0s[1:]:
                        if x - g[-1] <= col_tol:
                            g.append(x)
                        else:
                            raw_buckets.append(sum(g) / len(g))
                            g = [x]
                    raw_buckets.append(sum(g) / len(g))

                min_anchor_rows = max(2, int(len(anchor_rows) * 0.30))
                col_anchors = [
                    anchor for anchor in raw_buckets
                    if sum(
                        1 for row in anchor_rows
                        if any(abs(s["bbox"][0] - anchor) <= col_tol for s in row)
                    ) >= min_anchor_rows
                ]
                n_cols = len(col_anchors)
                if n_cols < 2:
                    continue

                # False positive guard: column spread
                if max(col_anchors) - min(col_anchors) < page_w * 0.05:
                    continue

                def _col_for(x0: float) -> int:
                    for i in range(n_cols - 1):
                        if x0 < col_anchors[i + 1] - col_tol / 2:
                            return i
                    return n_cols - 1

                grid: list = []
                grid_y0s: list = []
                for row, y0 in zip(region_rows, region_y0s):
                    cells = [''] * n_cols
                    for sp in row:
                        x0 = sp["bbox"][0]
                        ci = _col_for(x0)
                        txt = sp["text"].strip().replace('\n', ' ')
                        if txt:
                            cells[ci] = (cells[ci] + ' ' + txt).strip() if cells[ci] else txt
                    grid.append(cells)
                    grid_y0s.append(y0)

                # Phase 7: multi-line cell merging
                def _ends_with_word_hyphen(s: str) -> bool:
                    return bool(s) and s[-1] == '-' and len(s) >= 2 and s[-2].isalpha()

                def _merge_cells(prev: str, curr: str) -> str:
                    if not curr:
                        return prev
                    if _ends_with_word_hyphen(prev):
                        return prev[:-1] + curr
                    return (prev + ' ' + curr).strip()

                grid_ylast = list(grid_y0s)

                merged = True
                while merged:
                    merged = False
                    new_grid: list = [grid[0]]
                    new_y0s: list = [grid_y0s[0]]
                    new_ylast: list = [grid_ylast[0]]
                    for i in range(1, len(grid)):
                        non_empty = [(ci, v) for ci, v in enumerate(grid[i]) if v]

                        is_cont_a = (
                            len(non_empty) == 1
                            and sum(1 for v in new_grid[-1] if v) > 0
                            and new_grid[-1][non_empty[0][0]] != ''
                        )

                        y_gap = grid_y0s[i] - new_ylast[-1]
                        hyphen_cols = {
                            ci for ci, v in enumerate(new_grid[-1])
                            if _ends_with_word_hyphen(v)
                        }
                        curr_cols = {ci for ci, _ in non_empty}
                        prev_cols = {ci for ci, v in enumerate(new_grid[-1]) if v}
                        prev_is_partial = len(prev_cols) < n_cols
                        is_cont_b = (
                            not is_cont_a
                            and len(non_empty) > 1
                            and y_gap <= median_sz * 1.5
                            and len(hyphen_cols) >= 1
                            and bool(hyphen_cols & curr_cols)
                            and (
                                curr_cols.issubset(prev_cols)
                                or (prev_is_partial
                                    and hyphen_cols.issubset(curr_cols))
                            )
                        )

                        if is_cont_a:
                            ci, txt = non_empty[0]
                            new_grid[-1][ci] = _merge_cells(new_grid[-1][ci], txt)
                            new_ylast[-1] = grid_y0s[i]
                            merged = True
                        elif is_cont_b:
                            for ci in range(len(new_grid[-1])):
                                new_grid[-1][ci] = _merge_cells(
                                    new_grid[-1][ci], grid[i][ci]
                                )
                            new_ylast[-1] = grid_y0s[i]
                            merged = True
                        else:
                            new_grid.append(grid[i])
                            new_y0s.append(grid_y0s[i])
                            new_ylast.append(grid_ylast[i])
                    grid = new_grid
                    grid_y0s = new_y0s
                    grid_ylast = new_ylast

                grid = [r for r in grid if any(c for c in r)]

                if len(grid) < 2:
                    continue

                # False positive guard: list detection
                _BULLET_CHARS = frozenset({
                    '•', '·', '◦', '○', '▪', '▫', '▸', '►', '■', '□',
                    '‣', '◆', '◇', '–', '—', '―',
                })
                _ROMAN_SET = frozenset({
                    'i.', 'ii.', 'iii.', 'iv.', 'v.', 'vi.', 'vii.',
                    'viii.', 'ix.', 'x.', 'xi.', 'xii.', 'xiii.', 'xiv.',
                    'xv.', 'xvi.', 'xvii.', 'xviii.', 'xix.', 'xx.',
                })
                _SINGLE_LABEL = re.compile(r'^[a-z]\.$|^[0-9]\.$', re.IGNORECASE)

                def _col_is_list_labels(vals):
                    if len(vals) < 2:
                        return False
                    hits = sum(
                        1 for v in vals
                        if v in _BULLET_CHARS
                        or v.lower() in _ROMAN_SET
                        or bool(_SINGLE_LABEL.match(v))
                    )
                    return hits / len(vals) >= 0.5

                if any(
                    _col_is_list_labels(
                        [row[ci].strip() for row in grid if row[ci].strip()]
                    )
                    for ci in range(n_cols)
                ):
                    continue

                # Emit markdown
                table_y0 = grid_y0s[0] if grid_y0s else region_y0s[0]
                table_y1 = max(
                    s["bbox"][3] for row in region_rows for s in row
                )
                md_rows = []
                for i, row in enumerate(grid):
                    md_rows.append('| ' + ' | '.join(row) + ' |')
                    if i == 0:
                        md_rows.append('| ' + ' | '.join(['---'] * n_cols) + ' |')
                results.append((table_y0, table_y1, '\n'.join(md_rows)))

        except Exception as e:
            logger.debug(f"_cluster_spans_to_tables failed: {e}")

        return results
