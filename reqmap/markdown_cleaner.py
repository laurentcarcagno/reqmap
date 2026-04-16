"""
Markdown Cleaner Service

Cleans parsed markdown by removing unwanted content:
- Table of Contents
- List of Figures / Tables
- Headers / Footers
- Page numbers
- Revision history
- Index / Glossary
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class CleaningResult:
    """Result of markdown cleaning operation"""
    cleaned_text: str
    raw_text: str
    removed_sections: List[str] = field(default_factory=list)
    removed_lines_count: int = 0
    stats: Dict = field(default_factory=dict)


class MarkdownCleaner:
    """
    Clean parsed markdown by removing unwanted content.
    
    Detects and removes:
    - Table of Contents sections
    - List of Figures / Tables / Illustrations
    - Repeated headers and footers
    - Page numbers
    - Revision history / Document history
    - Index / Glossary sections
    """
    
    # Patterns for section headers to remove (case-insensitive)
    REMOVABLE_SECTION_PATTERNS = [
        # Table of Contents (EN/FR) — with or without heading markers
        r'^#{1,4}\s*(Table\s+of\s+Contents|Contents|Sommaire|Table\s+des\s+matières)\s*$',
        r'^\s*(Table\s+of\s+Contents|Sommaire|Table\s+des\s+matières)\s*$',
        # List of Figures/Tables/Images (EN/FR)
        r'^#{1,4}\s*(List\s+of\s+(Figures|Tables|Images|Pictures|Illustrations|Abbreviations|Acronyms|Equations))\s*$',
        r'^#{1,4}\s*(Table\s+of\s+(Figures|Tables|Images|Pictures|Illustrations))\s*$',
        r'^#{1,4}\s*(Liste\s+des\s+(Figures|Tableaux|Images|Illustrations|Abréviations|Acronymes))\s*$',
        # Non-heading variants (Docling sometimes omits #)
        r'^\s*(List\s+of\s+(Figures|Tables|Images|Pictures|Illustrations))\s*$',
        r'^\s*(Table\s+of\s+(Figures|Tables|Images|Pictures|Illustrations))\s*$',
        # Index / Glossary (EN/FR)
        r'^#{1,4}\s*(Index|Glossary|Glossaire)\s*$',
        # Bibliography (EN/FR)
        r'^#{1,4}\s*(Bibliography|Bibliographie|References|Références)\s*$',
        # Revision History
        r'^#{1,4}\s*(Revision\s+History|Document\s+History|Change\s+Log|Historique(\s+des\s+modifications)?)\s*$',
        # Appendices index
        r'^#{1,4}\s*(List\s+of\s+Appendices|Liste\s+des\s+Annexes)\s*$',
    ]
    
    # Patterns for individual lines to remove
    LINE_PATTERNS_TO_REMOVE = [
        # Page numbers in various formats
        r'^\s*Page\s+\d+\s*(of|/|sur|de)\s*\d+\s*$',
        r'^\s*-\s*\d+\s*-\s*$',                        # "- 123 -"
        r'^\s*—\s*\d+\s*—\s*$',                        # "— 123 —"
        r'^\s*\[\s*\d+\s*\]\s*$',                      # "[ 123 ]"
        r'^\s*\d+\s*/\s*\d+\s*$',                      # "12 / 45"
        # Standalone page numbers (be careful - only at line start/end)
        r'^\s*\d{1,4}\s*$',                            # Standalone "123"
        # Confidentiality / Draft markers
        r'^.*\b(CONFIDENTIAL|CONFIDENTIEL|DRAFT|BROUILLON|PROPRIETARY)\b.*$',
        # Copyright lines
        r'^\s*©.*\d{4}.*$',
        r'^\s*Copyright\s+©?\s*\d{4}.*$',
        # Document control lines
        r'^\s*(Document\s+No|Doc\s+No|Reference|Réf)\s*[:.]\s*[\w-]+\s*$',
        r'^\s*(Version|Rev|Revision)\s*[:.]\s*[\d.]+\s*$',
        r'^\s*(Date|Issue\s+Date)\s*[:.]\s*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\s*$',
    ]
    
    # TOC entry patterns (lines that look like TOC entries)
    TOC_ENTRY_PATTERNS = [
        r'^.{3,80}\.{3,}\s*\d+\s*$',          # "Section Name .......... 42"
        r'^.{3,80}\s+\.{3,}\s*\d+\s*$',       # "Section Name   .......... 42"
        r'^\d+(\.\d+)*\s+.{3,60}\s+\d+\s*$',  # "1.2.3 Section Name 42"
        r'^[A-Z]\.\d*\s+.{3,60}\s+\d+\s*$',   # "A.1 Appendix Name 42"
    ]
    
    # List of Figures/Tables/Images entry patterns
    LIST_ENTRY_PATTERNS = [
        r'^(Figure|Fig\.|Tableau|Table|Image|Picture|Illustration)\s+\d+[:.\-].{3,80}\.{2,}\s*\d+\s*$',
        r'^(Figure|Fig\.|Tableau|Table|Image|Picture|Illustration)\s+\d+[:.\-].{3,80}\s+\d+\s*$',
        r'^(Equation|Eq\.)\s+\d+[:.\-].{3,60}\.{2,}\s*\d+\s*$',
    ]
    
    def __init__(self, config: Dict = None):
        """
        Initialize cleaner with configuration.
        
        Config options:
            remove_toc: bool - Remove Table of Contents sections
            remove_list_of_figures: bool - Remove List of Figures sections
            remove_list_of_tables: bool - Remove List of Tables sections
            remove_headers_footers: bool - Remove detected headers/footers
            remove_page_numbers: bool - Remove page number lines
            remove_revision_history: bool - Remove revision history sections
            remove_index_glossary: bool - Remove index/glossary sections
            min_section_heading_level: int - Minimum heading level to detect sections (1-6)
        """
        self.config = config or {}
        
        # Feature flags
        self.remove_toc = self.config.get('remove_toc', True)
        self.remove_list_of_figures = self.config.get('remove_list_of_figures', True)
        self.remove_list_of_tables = self.config.get('remove_list_of_tables', True)
        self.remove_headers_footers = self.config.get('remove_headers_footers', True)
        self.remove_page_numbers = self.config.get('remove_page_numbers', True)
        self.remove_revision_history = self.config.get('remove_revision_history', True)
        self.remove_index_glossary = self.config.get('remove_index_glossary', True)
        
        # Compile patterns for efficiency
        self._compiled_section_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE) 
            for p in self.REMOVABLE_SECTION_PATTERNS
        ]
        self._compiled_line_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in self.LINE_PATTERNS_TO_REMOVE
        ]
        self._compiled_toc_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in self.TOC_ENTRY_PATTERNS
        ]
        self._compiled_list_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in self.LIST_ENTRY_PATTERNS
        ]
        
        logger.debug(f"MarkdownCleaner initialized with config: {self.config}")
    
    def clean(self, markdown: str) -> CleaningResult:
        """
        Clean markdown content by removing unwanted sections and lines.
        
        Args:
            markdown: Raw markdown text
            
        Returns:
            CleaningResult with cleaned text and statistics
        """
        raw_text = markdown
        removed_sections = []
        stats = {
            'original_lines': len(markdown.split('\n')),
            'original_chars': len(markdown),
            'sections_removed': 0,
            'lines_removed': 0,
            'toc_entries_removed': 0,
            'headings_inferred': 0,
        }
        
        # Strip page markers BEFORE infer_headings so they are not promoted to headings.
        # Matches lines like "Page 1 of 47", "F.1 Page 1 of 47", etc.
        if self.remove_page_numbers:
            _page_re = re.compile(r'^.*\bPage\s+\d+\s+(of|/|sur|de)\s+\d+\b.*$', re.IGNORECASE | re.MULTILINE)
            _before = len(markdown.split('\n'))
            markdown = _page_re.sub('', markdown)
            stats['lines_removed'] += _before - len(markdown.split('\n'))

        # Infer headings from numbered section patterns before any other processing
        markdown = self.infer_headings(markdown)
        stats['headings_inferred'] = markdown.count('\n#') - raw_text.count('\n#')
        
        lines = markdown.split('\n')
        cleaned_lines = []
        
        # State for section removal
        skip_until_next_heading = False
        current_section_level = 0
        current_section_name = ""
        
        for i, line in enumerate(lines):
            # Check if we should stop skipping (found a same-level or higher heading)
            if skip_until_next_heading:
                heading_match = re.match(r'^(#{1,6})\s+', line)
                if heading_match:
                    level = len(heading_match.group(1))
                    if level <= current_section_level:
                        # Found a heading at same or higher level, stop skipping
                        skip_until_next_heading = False
                        logger.debug(f"Stopped skipping at line {i}: {line[:50]}")
                    else:
                        # Still in the section, skip this line
                        stats['lines_removed'] += 1
                        continue
                else:
                    # Not a heading, still in section, skip
                    stats['lines_removed'] += 1
                    continue
            
            # Check if this line starts a removable section
            should_skip_section = False
            for pattern in self._compiled_section_patterns:
                if pattern.match(line.strip()):
                    heading_match = re.match(r'^(#{1,6})\s+', line)
                    current_section_level = len(heading_match.group(1)) if heading_match else 1
                    current_section_name = line.strip()
                    skip_until_next_heading = True
                    should_skip_section = True
                    removed_sections.append(current_section_name)
                    stats['sections_removed'] += 1
                    logger.info(f"Removing section: {current_section_name}")
                    break
            
            if should_skip_section:
                stats['lines_removed'] += 1
                continue
            
            # Check for TOC entry patterns
            is_toc_entry = False
            for pattern in self._compiled_toc_patterns:
                if pattern.match(line.strip()):
                    is_toc_entry = True
                    stats['toc_entries_removed'] += 1
                    stats['lines_removed'] += 1
                    break
            
            if is_toc_entry:
                continue
            
            # Check for List of Figures/Tables entry patterns
            is_list_entry = False
            for pattern in self._compiled_list_patterns:
                if pattern.match(line.strip()):
                    is_list_entry = True
                    stats['lines_removed'] += 1
                    break
            
            if is_list_entry:
                continue
            
            # Check for individual lines to remove (page numbers, etc.)
            line_removed = False
            if self.remove_page_numbers:
                for pattern in self._compiled_line_patterns:
                    if pattern.match(line.strip()):
                        stats['lines_removed'] += 1
                        line_removed = True
                        break
            
            if line_removed:
                continue
            
            # Line passed all filters, keep it
            cleaned_lines.append(line)
        
        # Join and clean up excessive blank lines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Repair malformed markdown tables
        cleaned_text = self.repair_markdown_tables(cleaned_text)
        
        # Remove more than 3 consecutive blank lines
        cleaned_text = re.sub(r'\n{4,}', '\n\n\n', cleaned_text)
        
        # Remove leading/trailing whitespace
        cleaned_text = cleaned_text.strip()
        
        # Final stats
        stats['final_lines'] = len(cleaned_text.split('\n'))
        stats['final_chars'] = len(cleaned_text)
        stats['lines_reduction_pct'] = round(
            (1 - stats['final_lines'] / max(stats['original_lines'], 1)) * 100, 1
        )
        stats['chars_reduction_pct'] = round(
            (1 - stats['final_chars'] / max(stats['original_chars'], 1)) * 100, 1
        )
        
        logger.info(
            f"Markdown cleaned: {stats['sections_removed']} sections removed, "
            f"{stats['lines_removed']} lines removed, "
            f"{stats['lines_reduction_pct']}% reduction"
        )
        
        return CleaningResult(
            cleaned_text=cleaned_text,
            raw_text=raw_text,
            removed_sections=removed_sections,
            removed_lines_count=stats['lines_removed'],
            stats=stats
        )
    
    def detect_repeated_content(
        self, 
        pages_text: List[str], 
        min_occurrences: int = 3
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect repeated headers and footers across pages.
        
        Checks single-line and multi-line (2-3 line) blocks at the
        top and bottom of each page.
        
        Args:
            pages_text: List of text content per page
            min_occurrences: Minimum times text must appear to be considered header/footer
            
        Returns:
            Tuple of (detected_header_pattern, detected_footer_pattern)
        """
        if len(pages_text) < min_occurrences:
            return None, None
        
        # Try multi-line blocks first (3, 2, then 1 line)
        header = None
        footer = None
        for n_lines in (3, 2, 1):
            first_blocks = []
            last_blocks = []
            for page in pages_text:
                lines = [l.strip() for l in page.split('\n') if l.strip()]
                if len(lines) >= n_lines * 2:  # enough lines for header+content or content+footer
                    first_blocks.append('\n'.join(lines[:n_lines]))
                    last_blocks.append('\n'.join(lines[-n_lines:]))

            if not header:
                header = self._find_repeated_pattern(first_blocks, min_occurrences)
            if not footer:
                footer = self._find_repeated_pattern(last_blocks, min_occurrences)
            if header and footer:
                break
        
        if header:
            logger.debug(f"Detected header pattern ({header.count(chr(10))+1} lines): {header[:60]}...")
        if footer:
            logger.debug(f"Detected footer pattern ({footer.count(chr(10))+1} lines): {footer[:60]}...")
        
        return header, footer

    def _find_repeated_pattern(
        self, 
        lines: List[str], 
        min_occurrences: int = 3
    ) -> Optional[str]:
        """
        Find text that appears repeatedly across lines.
        
        Normalizes numbers to # for pattern matching.
        """
        if not lines:
            return None
        
        # Normalize lines by replacing numbers with placeholder
        normalized = []
        original_map = {}
        
        for line in lines:
            # Skip very short lines
            if len(line) < 5:
                continue
            norm = re.sub(r'\d+', '#', line)
            normalized.append(norm)
            if norm not in original_map:
                original_map[norm] = line
        
        # Count occurrences
        counter = Counter(normalized)
        
        for pattern, count in counter.most_common(5):
            if count >= min_occurrences and len(pattern) > 10:
                return pattern
        
        return None
    
    def remove_pattern_from_text(
        self, 
        text: str, 
        pattern: str
    ) -> str:
        """
        Remove all lines (or multi-line blocks) matching a normalized pattern.
        
        Args:
            text: Input text
            pattern: Normalized pattern (with # for numbers), may contain \\n
            
        Returns:
            Text with matching lines/blocks removed
        """
        if not pattern:
            return text
        
        pattern_line_count = pattern.count('\n') + 1
        lines = text.split('\n')
        removed_count = 0
        
        if pattern_line_count == 1:
            # Single-line matching (original fast path)
            filtered_lines = []
            for line in lines:
                normalized = re.sub(r'\d+', '#', line.strip())
                if normalized != pattern:
                    filtered_lines.append(line)
                else:
                    removed_count += 1
        else:
            # Multi-line sliding window
            skip_until = 0
            filtered_lines = []
            for i, line in enumerate(lines):
                if i < skip_until:
                    continue
                if i + pattern_line_count <= len(lines):
                    block = '\n'.join(
                        l.strip() for l in lines[i:i + pattern_line_count]
                    )
                    normalized_block = re.sub(r'\d+', '#', block)
                    if normalized_block == pattern:
                        skip_until = i + pattern_line_count
                        removed_count += 1
                        continue
                filtered_lines.append(line)
        
        if removed_count > 0:
            logger.debug(f"Removed {removed_count} occurrences of pattern ({pattern_line_count} lines): {pattern[:40]}...")
        
        return '\n'.join(filtered_lines)
    
    def add_custom_section_pattern(self, pattern: str):
        """Add a custom regex pattern for sections to remove."""
        compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        self._compiled_section_patterns.append(compiled)
        logger.debug(f"Added custom section pattern: {pattern}")
    
    def add_custom_line_pattern(self, pattern: str):
        """Add a custom regex pattern for lines to remove."""
        compiled = re.compile(pattern, re.IGNORECASE)
        self._compiled_line_patterns.append(compiled)
        logger.debug(f"Added custom line pattern: {pattern}")
    
    def remove_header_footer_images(
        self, 
        text: str, 
        header_images: List[dict] = None,
        footer_images: List[dict] = None
    ) -> str:
        """
        Remove markdown image references that correspond to header/footer images.
        
        Matches images by dimensions (width x height) to identify header/footer logos.
        
        Args:
            text: Markdown text
            header_images: List of header image info dicts with 'width' and 'height'
            footer_images: List of footer image info dicts with 'width' and 'height'
            
        Returns:
            Text with header/footer image references removed
        """
        if not header_images and not footer_images:
            return text
        
        all_images = (header_images or []) + (footer_images or [])
        if not all_images:
            return text
        
        # Build set of image dimensions to match
        image_dimensions = set()
        for img_info in all_images:
            if img_info and 'width' in img_info and 'height' in img_info:
                # Round dimensions for fuzzy matching
                w = round(img_info['width'])
                h = round(img_info['height'])
                image_dimensions.add((w, h))
        
        if not image_dimensions:
            return text
        
        lines = text.split('\n')
        filtered_lines = []
        removed_count = 0
        
        # Pattern to match markdown images: ![alt text](path)
        img_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        
        for line in lines:
            # Check if line contains an image reference
            match = img_pattern.search(line.strip())
            if match:
                img_path = match.group(2)
                filename = img_path.split('/')[-1]
                
                # Heuristic: Remove images that are likely header/footer based on:
                # 1. Small dimensions in our detected set
                # 2. Common header/footer image naming patterns
                should_remove = False
                
                # Check if ANY of the detected dimensions are small (logo-sized)
                # Only remove if we have small dimensions AND this looks like a small image
                has_small_dimensions = any(w < 200 and h < 100 for w, h in image_dimensions)
                
                if has_small_dimensions:
                    for w, h in image_dimensions:
                        if w < 200 and h < 100:
                            if 'picture-' in filename.lower():
                                should_remove = True
                                break
                
                if should_remove:
                    removed_count += 1
                    logger.debug(f"Removing header/footer image: {filename}")
                    continue
            
            filtered_lines.append(line)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} header/footer image references")
        
        return '\n'.join(filtered_lines)

    # ------------------------------------------------------------------
    # Heading inference
    # ------------------------------------------------------------------
    @staticmethod
    def infer_headings(markdown: str) -> str:
        """Detect numbered section headings and convert them to markdown headings.

        Many PDF parsers (Docling, pymupdf4llm) fail to tag headings semantically
        when the PDF lacks proper structure tags.  This method recognises common
        numbered-section patterns and inserts the appropriate ``#`` prefix.

        Patterns handled
        ~~~~~~~~~~~~~~~~
        1. **Single-line** — number and title on the same line:
           ``1 Introduction``  →  ``# 1 Introduction``
           ``2.1 Scope``       →  ``## 2.1 Scope``

        2. **Split across two lines** — number on one line, title on the next:
           ``1.1\nScope``      →  ``## 1.1 Scope``

        Heading depth is derived from the dot-count of the section number:
           ``1``         → ``#``   (depth 1)
           ``1.1``       → ``##``  (depth 2)
           ``1.1.1``     → ``###`` (depth 3)
           ``1.1.1.1``+  → ``####`` (depth 4, capped)

        Lines that already start with ``#`` are left untouched.
        """
        lines = markdown.split('\n')
        out: list[str] = []
        headings_inferred = 0

        # Regex for a numbered section prefix: "1", "1.2", "1.2.3", "A.1", etc.
        # Each numeric segment must be 1–2 digits (avoids matching decimals like 1.623).
        # First digit must be 1–9 (section numbers never start with 0).
        _NUM_RE = re.compile(
            r'^(?P<num>'
            r'(?:[A-Z]\.)?'              # optional appendix letter (A.)
            r'[1-9]\d?(?:\.\d{1,2})*'   # 1  or  1.2  or  1.2.3 (first seg 1-99)
            r')'
            r'(?P<rest>\s.+)?$'          # optional: space + title text on same line
        )

        # Heuristic: a "title continuation" is a short-ish line that starts with
        # an uppercase letter and does NOT look like body text or a table cell.
        _TITLE_CONT_RE = re.compile(
            r'^[A-Z][A-Za-z][\w\s,/()&:;\'-]{0,80}$'
        )

        # Characters that suggest data/body text rather than a heading title
        _DATA_CHARS = set('%±°@$€£¥#<>=+[]{}|\\')

        def _heading_depth(num_str: str) -> int:
            """Return markdown heading depth (1–4) from section number."""
            dots = num_str.count('.')
            return min(dots + 1, 4)

        def _is_valid_title(text: str, num_str: str) -> bool:
            """Check whether 'text' looks like a genuine heading title."""
            # Must start with uppercase letter
            if not text or not text[0].isupper():
                return False
            # Single-word titles must be at least 4 chars (filters "Am2" but
            # allows "Introduction", "Mechanical", etc.)
            words = text.split()
            if len(words) == 1 and len(text) < 4:
                return False
            # Must be reasonably short
            if len(text) > 100:
                return False
            # Reject if it contains data characters (%, ±, °, etc.)
            if _DATA_CHARS.intersection(text):
                return False
            # For bare single-digit section numbers (1, 2, 3…) require even stricter:
            # title must be ≤ 60 chars — avoids footnotes like "2 Assumes 5% divergence…"
            if '.' not in num_str and len(text) > 60:
                return False
            return True

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip lines that are already markdown headings
            if stripped.startswith('#'):
                out.append(line)
                i += 1
                continue

            m = _NUM_RE.match(stripped)
            if m:
                num = m.group('num')
                rest = (m.group('rest') or '').strip()
                depth = _heading_depth(num)
                prefix = '#' * depth

                if rest:
                    # Single-line: "1 Introduction" or "2.1 Scope"
                    if _is_valid_title(rest, num):
                        out.append(f'{prefix} {num} {rest}')
                        headings_inferred += 1
                        i += 1
                        continue
                else:
                    # Number-only line — check if next non-blank line is the title
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines):
                        candidate = lines[j].strip()
                        if _TITLE_CONT_RE.match(candidate) and _is_valid_title(candidate, num):
                            out.append(f'{prefix} {num} {candidate}')
                            headings_inferred += 1
                            i = j + 1  # skip the title line we consumed
                            continue

            # Default: keep line as-is
            out.append(line)
            i += 1

        if headings_inferred:
            logger.info(f"Inferred {headings_inferred} section headings from numbered patterns")

        return '\n'.join(out)

    # ------------------------------------------------------------------
    # Markdown table post-processing
    # ------------------------------------------------------------------
    @staticmethod
    def repair_markdown_tables(markdown: str) -> str:
        """Validate and repair markdown tables in the text.

        Fixes:
        - Missing separator row (``| --- | --- |``) after header
        - Inconsistent column counts across rows
        - Rows with trailing/leading whitespace around pipes
        - Empty tables (removes them)

        Returns the repaired markdown string.
        """
        lines = markdown.split('\n')
        out_lines: List[str] = []
        table_buf: List[str] = []
        tables_fixed = 0

        def _is_table_row(line: str) -> bool:
            stripped = line.strip()
            return stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 2

        def _is_separator_row(line: str) -> bool:
            stripped = line.strip()
            if not (stripped.startswith('|') and stripped.endswith('|')):
                return False
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            return all(re.match(r'^:?-{1,}:?$', c) for c in cells if c)

        def _flush_table(buf: List[str]) -> List[str]:
            nonlocal tables_fixed
            if not buf:
                return []

            # Normalize each row: strip cells, ensure consistent pipes
            parsed_rows = []
            for row in buf:
                raw_cells = [c.strip() for c in row.strip().strip('|').split('|')]
                # Normalize cell content: remove 'None' literals, collapse <br> tags
                cells = []
                for cell in raw_cells:
                    if cell == 'None':
                        cell = ''
                    cell = re.sub(r'<br\s*/?>', ' ', cell, flags=re.IGNORECASE).strip()
                    cells.append(cell)
                parsed_rows.append(cells)

            if not parsed_rows:
                return []

            # Determine max columns
            max_cols = max(len(r) for r in parsed_rows)
            if max_cols == 0:
                return []

            # Pad rows to have consistent columns
            for i, row in enumerate(parsed_rows):
                while len(row) < max_cols:
                    row.append('')

            # Check if second row is a separator
            has_separator = len(parsed_rows) > 1 and all(
                re.match(r'^:?-{0,}:?$', c.strip()) for c in parsed_rows[1]
            ) and any('-' in c for c in parsed_rows[1])

            result = []
            # Header row
            header = '| ' + ' | '.join(parsed_rows[0]) + ' |'
            result.append(header)

            if not has_separator and len(parsed_rows) > 1:
                # Insert separator row
                sep = '| ' + ' | '.join(['---'] * max_cols) + ' |'
                result.append(sep)
                tables_fixed += 1
                data_start = 1
            else:
                if has_separator:
                    sep = '| ' + ' | '.join(['---'] * max_cols) + ' |'
                    result.append(sep)
                    data_start = 2
                else:
                    data_start = 1

            # Data rows
            for row in parsed_rows[data_start:]:
                result.append('| ' + ' | '.join(row) + ' |')

            return result

        for line in lines:
            if _is_table_row(line):
                table_buf.append(line)
            else:
                if table_buf:
                    repaired = _flush_table(table_buf)
                    if repaired:
                        out_lines.extend(repaired)
                    table_buf = []
                out_lines.append(line)

        # Flush any remaining table
        if table_buf:
            repaired = _flush_table(table_buf)
            if repaired:
                out_lines.extend(repaired)

        if tables_fixed:
            logger.info(f"Repaired {tables_fixed} markdown tables (added missing separators)")

        return '\n'.join(out_lines)
