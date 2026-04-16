"""Detect and OCR inline text-images embedded in PDFs.

Some PDFs embed requirement IDs, labels, or short text fragments as
raster images rather than selectable text.  Docling and PyMuPDF text
extraction silently skip these.

This module:
1. Scans each page for small image blocks (height < threshold).
2. Renders the page region at high DPI and runs RapidOCR.
3. Returns (page, y_position, ocr_text) tuples that callers can
   merge back into the extracted markdown.
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from rapidocr_onnxruntime import RapidOCR
    RAPIDOCR_AVAILABLE = True
except ImportError:
    RAPIDOCR_AVAILABLE = False

try:
    import numpy as np
    from PIL import Image
    IMAGING_AVAILABLE = True
except ImportError:
    IMAGING_AVAILABLE = False


class InlineTextImage:
    """A single inline text-image detected on a page."""

    __slots__ = ("page_num", "bbox", "ocr_text", "confidence",
                 "context_before", "context_after")

    def __init__(self, page_num: int, bbox: tuple, ocr_text: str,
                 confidence: float = 0.0,
                 context_before: str = "", context_after: str = ""):
        self.page_num = page_num
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.ocr_text = ocr_text
        self.confidence = confidence
        self.context_before = context_before
        self.context_after = context_after

    def __repr__(self):
        return (f"InlineTextImage(page={self.page_num}, "
                f"text={self.ocr_text!r}, conf={self.confidence:.2f})")


class InlineImageOCR:
    """Detect and OCR small inline text-images in a PDF."""

    # Inline text-image heuristics
    MAX_IMAGE_HEIGHT = 18      # points – typical single-line text image
    MIN_IMAGE_WIDTH = 20       # points – skip tiny decorative dots
    RENDER_DPI = 300           # DPI for rendering page clips
    MIN_OCR_CONFIDENCE = 0.60  # drop low-confidence garbage
    # Ignore images whose top is in the top/bottom N% of page (header/footer zone)
    HEADER_ZONE_PCT = 0.10
    FOOTER_ZONE_PCT = 0.92

    def __init__(self, max_height: float = None, render_dpi: int = None,
                 min_confidence: float = None):
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF (fitz) is required for InlineImageOCR")
        if not RAPIDOCR_AVAILABLE:
            raise ImportError("rapidocr_onnxruntime is required for InlineImageOCR")
        if not IMAGING_AVAILABLE:
            raise ImportError("numpy and Pillow are required for InlineImageOCR")

        self.max_height = max_height or self.MAX_IMAGE_HEIGHT
        self.render_dpi = render_dpi or self.RENDER_DPI
        self.min_confidence = min_confidence or self.MIN_OCR_CONFIDENCE
        self._ocr = RapidOCR()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_inline_texts(self, pdf_path: Path) -> List[InlineTextImage]:
        """Scan a PDF and return OCR'd inline text-images.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of InlineTextImage objects sorted by (page, y).
        """
        doc = fitz.open(str(pdf_path))
        results: List[InlineTextImage] = []

        try:
            for page_idx in range(doc.page_count):
                page = doc[page_idx]
                page_results = self._process_page(page, page_idx + 1)
                results.extend(page_results)
        finally:
            doc.close()

        results.sort(key=lambda r: (r.page_num, r.bbox[1], r.bbox[0]))

        # Merge adjacent fragments on the same line into single items
        # e.g. "HAR SSOW-1" + "Inputs" → "HAR SSOW-1 / Inputs"
        results = self._merge_adjacent(results)

        logger.info(
            f"InlineImageOCR: {len(results)} text-images OCR'd from "
            f"{pdf_path.name}"
        )
        return results

    def inject_into_markdown(self, markdown: str,
                             items: List[InlineTextImage]) -> str:
        """Insert OCR'd text into markdown at the correct positions.

        Strategy:
        1. Replace mangled lines produced by pymupdf4llm's built-in OCR
           (e.g. ``## HARSSOW-3/Subcontractorresponsibilities``) with the
           correct OCR text (e.g. ``HAR SSOW-3 / Subcontractor responsibilities``).
        2. For items that had no mangled counterpart, fall back to the
           context-based insertion strategy.
        """
        if not items:
            return markdown

        replaced, remaining = self._replace_mangled(markdown, items)
        markdown = replaced

        injected = 0
        for item in remaining:
            if not item.ocr_text.strip():
                continue

            markdown, did_inject = self._inject_single(markdown, item)
            if did_inject:
                injected += 1
            else:
                logger.debug(
                    f"Could not place OCR text {item.ocr_text!r} "
                    f"(page {item.page_num}) — context not found"
                )

        total = len(items) - len(remaining) + injected
        logger.info(f"InlineImageOCR: injected {total}/{len(items)} "
                     f"text-images into markdown")
        return markdown

    @staticmethod
    def _compress(text: str) -> str:
        """Strip all non-alphanumeric chars for fuzzy matching."""
        return re.sub(r'[^A-Za-z0-9]', '', text).upper()

    # Regex to extract requirement ID number from a line (e.g. "SSOW-21" → "21")
    _REQ_ID_RE = re.compile(r'SSOW-(\d+)', re.IGNORECASE)

    def _replace_mangled(
        self, markdown: str, items: List[InlineTextImage]
    ) -> Tuple[str, List[InlineTextImage]]:
        """Replace mangled OCR lines in markdown with correct OCR text.

        pymupdf4llm's built-in OCR collapses spaces and adds ``##`` prefixes,
        e.g. ``## HARSSOW-3/Subcontractorresponsibilities``.  We detect these
        by matching on the requirement ID number (e.g. ``21`` from ``SSOW-21``),
        which is stable across both the mangled and our OCR output.

        Returns (updated_markdown, unmatched_items) where unmatched_items are
        items that had no mangled line to replace (injected via context instead).
        """
        # Build lookup: req_id_number -> item  (e.g. "21" -> item)
        id_to_item: dict = {}
        for item in items:
            m = self._REQ_ID_RE.search(item.ocr_text)
            if m:
                id_to_item[m.group(1)] = item

        lines = markdown.split('\n')
        new_lines = []
        replaced_ids: set = set()

        for line in lines:
            m = self._REQ_ID_RE.search(line)
            if m:
                req_id = m.group(1)
                matched_item = id_to_item.get(req_id)
                if matched_item is not None:
                    # Only replace lines that look like mangled OCR headings
                    # (no spaces in the title part, or ## prefix from pymupdf4llm)
                    stripped = line.strip().lstrip('#').strip()
                    has_no_spaces_in_title = '/' in stripped and ' ' not in stripped.split('/')[-1]
                    has_heading_prefix = line.strip().startswith('#')
                    if has_no_spaces_in_title or has_heading_prefix:
                        new_lines.append(matched_item.ocr_text.strip())
                        replaced_ids.add(req_id)
                        logger.debug(f"Replaced mangled line {line.strip()!r} "
                                     f"→ {matched_item.ocr_text.strip()!r}")
                        continue
            new_lines.append(line)

        updated = '\n'.join(new_lines)
        remaining = [item for item in items
                     if self._REQ_ID_RE.search(item.ocr_text) and
                     self._REQ_ID_RE.search(item.ocr_text).group(1) not in replaced_ids]
        logger.debug(f"_replace_mangled: {len(replaced_ids)} lines replaced, "
                     f"{len(remaining)} items remaining for context injection")
        return updated, remaining

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _merge_adjacent(self, items: List[InlineTextImage]) -> List[InlineTextImage]:
        """Merge adjacent inline text-images on the same y-line into one.

        Requirement IDs are often split across two images:
        e.g. "HAR SSOW-1" (image 1) + "Inputs" (image 2) → "HAR SSOW-1 / Inputs"
        """
        if len(items) < 2:
            return items

        merged: List[InlineTextImage] = []
        i = 0
        while i < len(items):
            current = items[i]
            # Look ahead and merge items on the same page with similar y
            while i + 1 < len(items):
                nxt = items[i + 1]
                same_page = nxt.page_num == current.page_num
                # Same line: y-centers within 6 points of each other
                cur_y = (current.bbox[1] + current.bbox[3]) / 2
                nxt_y = (nxt.bbox[1] + nxt.bbox[3]) / 2
                same_line = abs(cur_y - nxt_y) < 6.0

                if same_page and same_line:
                    # Combine text: add " / " separator if not already present
                    cur_text = current.ocr_text.rstrip()
                    nxt_text = nxt.ocr_text.lstrip()
                    if cur_text.endswith('/'):
                        combined = cur_text + ' ' + nxt_text
                    elif nxt_text.startswith('/'):
                        combined = cur_text + ' ' + nxt_text
                    else:
                        combined = cur_text + ' / ' + nxt_text
                    # Clean up double slashes or extra spaces
                    combined = combined.replace(' /  / ', ' / ')

                    current = InlineTextImage(
                        page_num=current.page_num,
                        bbox=(current.bbox[0], current.bbox[1],
                              nxt.bbox[2], nxt.bbox[3]),
                        ocr_text=combined,
                        confidence=min(current.confidence, nxt.confidence),
                        context_before=current.context_before,
                        context_after=nxt.context_after or current.context_after,
                    )
                    i += 1
                else:
                    break

            merged.append(current)
            i += 1

        if len(merged) < len(items):
            logger.debug(f"Merged {len(items)} fragments → {len(merged)} items")

        # Normalize merged text: ensure "HAR SSOW-N" always comes first
        for item in merged:
            item.ocr_text = self._normalize_req_id(item.ocr_text)

        # Deduplicate: remove items with identical (page, ocr_text)
        seen = set()
        deduped = []
        for item in merged:
            key = (item.page_num, item.ocr_text)
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        if len(deduped) < len(merged):
            logger.debug(f"Deduped {len(merged)} → {len(deduped)} items")
        return deduped

    @staticmethod
    def _normalize_req_id(text: str) -> str:
        """Ensure requirement ID (HAR SSOW-N) is always before the title.

        Also cleans stray single-char OCR artifacts from title text.
        """
        # Pattern: "Title text / HAR SSOW-N" → "HAR SSOW-N / Title text"
        m = re.match(
            r'^(.+?)\s*/\s*(HAR\s+SSOW-\d+)(.*)$', text
        )
        if m:
            title_part = m.group(1).strip()
            id_part = m.group(2).strip()
            rest = m.group(3).strip()
            if rest:
                title_part = title_part + ' ' + rest
            text = f"{id_part} / {title_part}"

        # Remove stray single "I" in title: "Mechanical detail I design" → "Mechanical detail design"
        # These come from OCR picking up a fragment of the "/" separator
        text = re.sub(r'(\b\w{2,})\s+I\s+(\w{2,}\b)', r'\1 \2', text)

        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _process_page(self, page, page_num: int) -> List[InlineTextImage]:
        """Find and OCR inline text-images on a single page."""
        page_height = page.rect.height
        header_y = page_height * self.HEADER_ZONE_PCT
        footer_y = page_height * self.FOOTER_ZONE_PCT

        blocks = page.get_text("dict")["blocks"]

        # Separate text blocks and candidate image blocks
        text_blocks = []  # (y_mid, text_snippet)
        image_candidates = []  # bbox tuples

        for b in blocks:
            if b["type"] == 0:
                # Text block — extract a short snippet for context
                lines = b.get("lines", [])
                for line in lines:
                    txt = " ".join(
                        s.get("text", "").strip() for s in line.get("spans", [])
                        if s.get("text", "").strip()
                    )
                    if txt:
                        y_mid = (line["bbox"][1] + line["bbox"][3]) / 2
                        text_blocks.append((y_mid, txt))
            elif b["type"] == 1:
                bbox = b["bbox"]
                h = bbox[3] - bbox[1]
                w = bbox[2] - bbox[0]
                y_top = bbox[1]
                # Filter: small height, reasonable width, not in header/footer
                if (h <= self.max_height and w >= self.MIN_IMAGE_WIDTH
                        and y_top > header_y and y_top < footer_y):
                    image_candidates.append(tuple(bbox))

        if not image_candidates:
            return []

        # Sort text blocks by y for context lookup
        text_blocks.sort(key=lambda t: t[0])

        results = []
        for bbox in image_candidates:
            img_y_mid = (bbox[1] + bbox[3]) / 2

            # Render page clip at high DPI and OCR
            ocr_text, confidence = self._ocr_region(page, bbox)
            if not ocr_text or confidence < self.min_confidence:
                continue

            # Find nearest text before and after the image
            ctx_before = self._find_context(text_blocks, img_y_mid, before=True)
            ctx_after = self._find_context(text_blocks, img_y_mid, before=False)

            results.append(InlineTextImage(
                page_num=page_num,
                bbox=bbox,
                ocr_text=ocr_text.strip(),
                confidence=confidence,
                context_before=ctx_before,
                context_after=ctx_after,
            ))

        return results

    def _ocr_region(self, page, bbox: tuple) -> Tuple[str, float]:
        """Render a page clip at high DPI and OCR it. Returns (text, avg_confidence)."""
        pad = 4
        clip = fitz.Rect(
            bbox[0] - pad, bbox[1] - pad,
            bbox[2] + pad, bbox[3] + pad
        )
        pix = page.get_pixmap(clip=clip, dpi=self.RENDER_DPI)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        if pix.n == 4:
            img_array = img_array[:, :, :3]

        result, _ = self._ocr(img_array)
        if not result:
            return "", 0.0

        # Combine all detected text fragments
        texts = []
        confs = []
        for detection in result:
            # Each detection: [bbox_points, text, confidence]
            texts.append(detection[1])
            confs.append(detection[2])

        combined = " ".join(texts)
        avg_conf = sum(confs) / len(confs) if confs else 0.0

        # Clean up common OCR artifacts
        combined = re.sub(r'\s+', ' ', combined).strip()
        # Fix split requirement IDs: "HAR SSOW - 1" → "HAR SSOW-1"
        combined = re.sub(r'(\w)\s*-\s*(\d)', r'\1-\2', combined)
        # Remove trailing OCR artifacts on ID images: "HAR SSOW-7/I" → "HAR SSOW-7"
        # The small ID image sometimes picks up the start of the slash or next char
        combined = re.sub(r'(HAR\s+SSOW-\d+)\s*/\s*[A-Z]?$', r'\1', combined)
        # Also handle "HAR SSOW-5 /" → "HAR SSOW-5"
        combined = re.sub(r'(HAR\s+SSOW-\d+)\s*/$', r'\1', combined)
        # Fix "1 / Inputs" being duplicated from overlapping detections
        combined = re.sub(r'(\d+)\s*/\s*', r'\1 / ', combined)
        # Remove leading duplicate number from split detections
        # e.g. "HAR SSOW-1 1 / Inputs" → "HAR SSOW-1 / Inputs"
        combined = re.sub(r'(\w+-\d+)\s+\d+\s*/\s*', r'\1 / ', combined)
        # Remove stray leading " / I " artifacts from mechanical design labels
        combined = re.sub(r'\s*/\s*I\s+/', ' / ', combined)

        return combined, avg_conf

    def _find_context(self, text_blocks: list, y: float,
                      before: bool) -> str:
        """Find the nearest text line above or below position y."""
        best = None
        best_dist = float('inf')

        for y_mid, txt in text_blocks:
            if before and y_mid < y:
                dist = y - y_mid
                if dist < best_dist:
                    best_dist = dist
                    best = txt
            elif not before and y_mid > y:
                dist = y_mid - y
                if dist < best_dist:
                    best_dist = dist
                    best = txt

        # Truncate to a usable snippet for matching
        if best:
            best = best[:120].strip()
        return best or ""

    def _inject_single(self, markdown: str,
                       item: InlineTextImage) -> Tuple[str, bool]:
        """Try to inject a single OCR'd text into the markdown.

        Returns (updated_markdown, success).
        """
        ocr_line = item.ocr_text.strip()
        if not ocr_line:
            return markdown, False

        # Check if the OCR text is already present in the markdown
        if ocr_line in markdown:
            return markdown, False
        # Also check without spaces around slash
        normalized = re.sub(r'\s*/\s*', ' / ', ocr_line)
        if normalized in markdown:
            return markdown, False

        # Strategy 1: Find context_before in markdown and insert after it
        if item.context_before:
            snippet = self._make_search_snippet(item.context_before)
            if snippet:
                pos = markdown.find(snippet)
                if pos >= 0:
                    # Find end of the line containing context_before
                    line_end = markdown.find('\n', pos)
                    if line_end < 0:
                        line_end = len(markdown)
                    # Insert OCR text on new line after context_before
                    new_md = (markdown[:line_end] + '\n\n'
                              + ocr_line + '\n'
                              + markdown[line_end:])
                    return new_md, True

        # Strategy 2: Find context_after and insert before it
        if item.context_after:
            snippet = self._make_search_snippet(item.context_after)
            if snippet:
                pos = markdown.find(snippet)
                if pos >= 0:
                    # Find start of the line containing context_after
                    line_start = markdown.rfind('\n', 0, pos)
                    if line_start < 0:
                        line_start = 0
                    new_md = (markdown[:line_start] + '\n'
                              + ocr_line + '\n'
                              + markdown[line_start:])
                    return new_md, True

        return markdown, False

    def _make_search_snippet(self, text: str) -> str:
        """Create a search-friendly snippet from context text.

        Takes the first ~60 chars, but avoids cutting mid-word.
        """
        if not text:
            return ""
        # Use first meaningful portion
        snippet = text[:80]
        # Try to cut at word boundary
        if len(text) > 80:
            space = snippet.rfind(' ')
            if space > 30:
                snippet = snippet[:space]
        return snippet.strip()
