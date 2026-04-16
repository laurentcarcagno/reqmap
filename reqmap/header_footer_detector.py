"""
Header/Footer Detection Service

Detects repeating headers and footers (text and images) in PDF documents
using PyMuPDF position-based analysis.
"""

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import re

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    import numpy as np
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF or numpy not available. Header/footer detection disabled.")


@dataclass
class TextBlock:
    """Text block with position and properties."""
    bbox: Tuple[float, float, float, float]  # x0,y0,x1,y1
    text: str
    font: str
    size: float
    flags: int
    page_num: int


@dataclass
class ImageBlock:
    """Image block with position and properties."""
    bbox: Tuple[float, float, float, float]  # x0,y0,x1,y1
    width: float
    height: float
    page_num: int
    xref: int


@dataclass
class TableBlock:
    """Table block with position and properties."""
    bbox: Tuple[float, float, float, float]  # x0,y0,x1,y1
    rows: int
    cols: int
    page_num: int


@dataclass
class HeaderFooter:
    """Detected header/footer info."""
    type: str  # "header" or "footer"
    content_type: str  # "text" or "image"
    text: str  # empty for images
    bbox: Tuple[float, float, float, float]
    frequency: int
    avg_y: float  # normalized position (0-1)
    image_info: dict = None  # width, height, xref for images
    id: str = ""  # stable identifier, e.g. "header_text_0"
    per_page_bboxes: Dict[int, List[List[float]]] = field(default_factory=dict)


class HeaderFooterDetector:
    """
    Detect repeating headers and footers in PDF documents.
    
    Uses position-based analysis to find text and images that appear
    consistently in the top or bottom margins across multiple pages.
    """
    
    def __init__(self):
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF and numpy required for header/footer detection")
        
        self.blocks: List[TextBlock] = []
        self.image_blocks: List[ImageBlock] = []
        self.table_blocks: List[TableBlock] = []
        self.headers_footers: List[HeaderFooter] = []
        self.page_heights = []
    
    @staticmethod
    def normalize_text(t: str) -> str:
        """Normalize text for comparison."""
        return " ".join(t.lower().split())
    
    def detect(self, pdf_path: str, threshold_pages: int = 3, 
               top_bottom_pct: float = 0.10) -> List[HeaderFooter]:
        """
        Detect headers and footers in a PDF.
        
        Args:
            pdf_path: Path to PDF file
            threshold_pages: Minimum pages for detection (default: 3)
            top_bottom_pct: Top/bottom zone size as fraction (default: 0.10 = 10%)
            
        Returns:
            List of detected HeaderFooter objects
        """
        self.blocks = []
        self.image_blocks = []
        self.table_blocks = []
        self.headers_footers = []
        self.page_heights = []
        
        try:
            doc = fitz.open(pdf_path)
            
            if doc.page_count < threshold_pages:
                logger.debug(f"PDF has {doc.page_count} pages, less than threshold {threshold_pages}")
                doc.close()
                return []
            
            logger.debug(f"Analyzing {doc.page_count} pages for headers/footers...")
            
            # Extract text and image blocks
            self._extract_blocks(doc)
            
            # Detect repeating patterns
            self._detect_patterns(threshold_pages, top_bottom_pct, doc.page_count)
            
            doc.close()
            
            logger.info(f"Detected {len(self.headers_footers)} header/footer patterns "
                       f"({sum(1 for hf in self.headers_footers if hf.content_type == 'text')} text, "
                       f"{sum(1 for hf in self.headers_footers if hf.content_type == 'image')} image)")
            
            return self.headers_footers
            
        except Exception as e:
            logger.error(f"Error detecting headers/footers: {e}")
            return []
    
    def _extract_blocks(self, doc) -> None:
        """Extract all text and image blocks from document."""
        for page_num in range(doc.page_count):
            page = doc[page_num]
            self.page_heights.append(page.rect.height)
            
            # Extract text blocks
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if len(text) < 2:
                            continue
                        
                        self.blocks.append(TextBlock(
                            bbox=span["bbox"],
                            text=text,
                            font=span["font"],
                            size=span["size"],
                            flags=span["flags"],
                            page_num=page_num
                        ))
            
            # Extract images
            image_list = page.get_images(full=True)
            for img in image_list:
                xref = img[0]
                try:
                    img_rects = page.get_image_rects(xref)
                    for rect in img_rects:
                        self.image_blocks.append(ImageBlock(
                            bbox=(rect.x0, rect.y0, rect.x1, rect.y1),
                            width=rect.width,
                            height=rect.height,
                            page_num=page_num,
                            xref=xref
                        ))
                except Exception:
                    pass

            # Extract tables via PyMuPDF table finder (requires PyMuPDF >= 1.23)
            try:
                tab_finder = page.find_tables()
                for tab in tab_finder.tables:
                    r = tab.bbox
                    rows = max(0, len(tab.rows) - 1) if hasattr(tab, 'rows') and tab.rows else 0
                    cols = max(0, len(tab.cols) - 1) if hasattr(tab, 'cols') and tab.cols else 0
                    if rows == 0 or cols == 0:
                        try:
                            cells = tab.extract()
                            if cells:
                                rows = rows or len(cells)
                                cols = cols or (len(cells[0]) if cells[0] else 0)
                        except Exception:
                            pass
                    self.table_blocks.append(TableBlock(
                        bbox=(r[0], r[1], r[2], r[3]),
                        rows=rows,
                        cols=cols,
                        page_num=page_num,
                    ))
            except Exception:
                pass
        
        logger.debug(
            f"Extracted {len(self.blocks)} text blocks, "
            f"{len(self.image_blocks)} images, "
            f"{len(self.table_blocks)} tables"
        )
    
    def _detect_patterns(self, threshold_pages: int, zone_pct: float, total_pages: int) -> None:
        """Detect repeating patterns in top/bottom zones."""
        top_blocks = []
        bottom_blocks = []
        top_images = []
        bottom_images = []
        top_tables = []
        bottom_tables = []
        
        for block in self.blocks:
            page_height = self.page_heights[block.page_num]
            norm_y0 = block.bbox[1] / page_height
            norm_y1 = block.bbox[3] / page_height

            if norm_y0 < zone_pct:
                top_blocks.append(block)
            if norm_y1 > (1.0 - zone_pct):
                bottom_blocks.append(block)

        for img in self.image_blocks:
            page_height = self.page_heights[img.page_num]
            norm_y0 = img.bbox[1] / page_height
            norm_y1 = img.bbox[3] / page_height

            if norm_y0 < zone_pct:
                top_images.append(img)
            if norm_y1 > (1.0 - zone_pct):
                bottom_images.append(img)

        for tab in self.table_blocks:
            page_height = self.page_heights[tab.page_num]
            norm_y0 = tab.bbox[1] / page_height
            norm_y1 = tab.bbox[3] / page_height

            if norm_y0 < zone_pct:
                top_tables.append(tab)
            if norm_y1 > (1.0 - zone_pct):
                bottom_tables.append(tab)
        
        logger.debug(
            f"Top zone: {len(top_blocks)} text, {len(top_images)} images, {len(top_tables)} tables | "
            f"Bottom zone: {len(bottom_blocks)} text, {len(bottom_images)} images, {len(bottom_tables)} tables"
        )
        
        # Analyze text zones
        top_counter = Counter(self.normalize_text(b.text) for b in top_blocks)
        bottom_counter = Counter(self.normalize_text(b.text) for b in bottom_blocks)
        
        self._analyze_text_zone(top_blocks, top_counter, "header", threshold_pages, total_pages)
        self._analyze_text_zone(bottom_blocks, bottom_counter, "footer", threshold_pages, total_pages)
        
        # Analyze image zones
        self._analyze_image_zone(top_images, "header", threshold_pages, total_pages)
        self._analyze_image_zone(bottom_images, "footer", threshold_pages, total_pages)

        # Analyze table zones
        self._analyze_table_zone(top_tables, "header", threshold_pages, total_pages)
        self._analyze_table_zone(bottom_tables, "footer", threshold_pages, total_pages)
    
    def _analyze_text_zone(self, blocks: List[TextBlock], counter: Counter, 
                          zone_type: str, threshold_pages: int, total_pages: int) -> None:
        """Analyze text blocks in a zone."""
        candidates = counter.most_common()
        page_texts = defaultdict(list)
        
        for block in blocks:
            norm_text = self.normalize_text(block.text)
            page_texts[block.page_num].append(norm_text)
        
        for norm_text, total_count in candidates:
            if total_count < threshold_pages:
                continue
            
            pages_with_text = set()
            avg_y = []
            
            for page_num, page_texts_list in page_texts.items():
                if norm_text in page_texts_list:
                    pages_with_text.add(page_num)
                    page_zone_blocks = [b for b in blocks if b.page_num == page_num and 
                                      self.normalize_text(b.text) == norm_text]
                    if page_zone_blocks:
                        avg_y.append(np.mean([b.bbox[3] / self.page_heights[page_num] 
                                            for b in page_zone_blocks]))
            
            unique_pages = len(pages_with_text)
            if unique_pages >= threshold_pages:
                rep_block = max((b for b in blocks if self.normalize_text(b.text) == norm_text), 
                              key=lambda b: b.size)

                ppb: Dict[int, List[List[float]]] = {}
                for page_num in pages_with_text:
                    matching = [b for b in blocks
                                if b.page_num == page_num
                                and self.normalize_text(b.text) == norm_text]
                    if matching:
                        ppb[page_num] = [list(b.bbox) for b in matching]

                hf_id = f"{zone_type}_text_{len(self.headers_footers)}"
                self.headers_footers.append(HeaderFooter(
                    type=zone_type,
                    content_type="text",
                    text=rep_block.text,
                    bbox=rep_block.bbox,
                    frequency=unique_pages,
                    avg_y=np.mean(avg_y) if avg_y else 0,
                    image_info=None,
                    id=hf_id,
                    per_page_bboxes=ppb,
                ))
                
                logger.debug(f"{zone_type.upper()} (text): '{rep_block.text[:40]}...' "
                           f"on {unique_pages}/{total_pages} pages")
    
    def _analyze_image_zone(self, images: List[ImageBlock], zone_type: str, 
                           threshold_pages: int, total_pages: int) -> None:
        """Analyze images in a zone."""
        if not images:
            return
        
        # Group images by position and size
        image_groups = defaultdict(list)
        
        for img in images:
            page_height = self.page_heights[img.page_num]
            norm_y = img.bbox[1] / page_height
            pos_key = (round(norm_y * 50) / 50, round(img.width), round(img.height))
            image_groups[pos_key].append(img)
        
        # Find repeating images
        for pos_key, img_list in image_groups.items():
            pages_with_img = set(img.page_num for img in img_list)
            unique_pages = len(pages_with_img)
            
            if unique_pages >= threshold_pages:
                rep_img = img_list[0]
                avg_y = np.mean([img.bbox[3] / self.page_heights[img.page_num] for img in img_list])

                ppb: Dict[int, List[List[float]]] = {}
                for page_num in pages_with_img:
                    ppb[page_num] = [list(img.bbox) for img in img_list
                                     if img.page_num == page_num]

                hf_id = f"{zone_type}_image_{len(self.headers_footers)}"
                self.headers_footers.append(HeaderFooter(
                    type=zone_type,
                    content_type="image",
                    text="",
                    bbox=rep_img.bbox,
                    frequency=unique_pages,
                    avg_y=avg_y,
                    image_info={
                        "width": rep_img.width,
                        "height": rep_img.height,
                        "xref": rep_img.xref
                    },
                    id=hf_id,
                    per_page_bboxes=ppb,
                ))
                
                logger.debug(f"{zone_type.upper()} (image): {rep_img.width:.0f}x{rep_img.height:.0f}px "
                           f"on {unique_pages}/{total_pages} pages")

    def _analyze_table_zone(self, tables: List[TableBlock], zone_type: str,
                            threshold_pages: int, total_pages: int) -> None:
        """Analyze tables in a zone for repeating patterns."""
        if not tables:
            return

        table_groups: Dict[tuple, List[TableBlock]] = defaultdict(list)
        for tab in tables:
            page_height = self.page_heights[tab.page_num]
            norm_y = round((tab.bbox[1] / page_height) * 20) / 20
            width  = round((tab.bbox[2] - tab.bbox[0]) / 10) * 10
            height = round((tab.bbox[3] - tab.bbox[1]) / 10) * 10
            key = (norm_y, width, height)
            table_groups[key].append(tab)

        for key, tab_list in table_groups.items():
            pages_with_table = set(t.page_num for t in tab_list)
            unique_pages = len(pages_with_table)

            if unique_pages >= threshold_pages:
                rep_tab = tab_list[0]
                avg_y = np.mean([t.bbox[3] / self.page_heights[t.page_num] for t in tab_list])

                ppb: Dict[int, List[List[float]]] = {}
                for page_num in pages_with_table:
                    ppb[page_num] = [list(t.bbox) for t in tab_list
                                     if t.page_num == page_num]

                hf_id = f"{zone_type}_table_{len(self.headers_footers)}"
                self.headers_footers.append(HeaderFooter(
                    type=zone_type,
                    content_type="table",
                    text="",
                    bbox=rep_tab.bbox,
                    frequency=unique_pages,
                    avg_y=avg_y,
                    image_info={
                        "rows": rep_tab.rows,
                        "cols": rep_tab.cols,
                    },
                    id=hf_id,
                    per_page_bboxes=ppb,
                ))

                logger.debug(
                    f"{zone_type.upper()} (table): {rep_tab.rows}r×{rep_tab.cols}c "
                    f"on {unique_pages}/{total_pages} pages"
                )

    def get_text_patterns(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract normalized text patterns for header/footer removal.
        
        Returns patterns compatible with MarkdownCleaner.remove_pattern_from_text()
        where numbers are replaced with '#' for pattern matching.
        
        Returns:
            Tuple of (header_pattern, footer_pattern) or (None, None)
        """
        headers = [hf for hf in self.headers_footers 
                  if hf.type == "header" and hf.content_type == "text"]
        footers = [hf for hf in self.headers_footers 
                  if hf.type == "footer" and hf.content_type == "text"]
        
        header_pattern = None
        if headers:
            most_frequent_header = max(headers, key=lambda hf: hf.frequency)
            header_pattern = re.sub(r'\d+', '#', most_frequent_header.text.strip())
            logger.debug(f"Header pattern: {header_pattern}")
        
        footer_pattern = None
        if footers:
            most_frequent_footer = max(footers, key=lambda hf: hf.frequency)
            footer_pattern = re.sub(r'\d+', '#', most_frequent_footer.text.strip())
            logger.debug(f"Footer pattern: {footer_pattern}")
        
        return header_pattern, footer_pattern
    
    def get_image_patterns(self) -> Tuple[List[dict], List[dict]]:
        """
        Extract image patterns for header/footer removal.
        
        Returns:
            Tuple of (header_images, footer_images) where each is a list of dicts
            containing image info (width, height, xref)
        """
        header_images = [hf.image_info for hf in self.headers_footers 
                        if hf.type == "header" and hf.content_type == "image" and hf.image_info]
        footer_images = [hf.image_info for hf in self.headers_footers 
                        if hf.type == "footer" and hf.content_type == "image" and hf.image_info]
        
        return header_images, footer_images
