# ReqMap

**PDF → Clean Markdown → Structured JSON** extraction framework for requirement documents.

Takes a PDF as input and produces:
1. A raw markdown file (direct pymupdf4llm output, cleaned of headers/footers and OCR artefacts)
2. A clean markdown file (further cleaned: TOC removed, headings inferred, tables repaired)
3. Optionally, a structured JSON file of ordered title and requirement nodes — ready for traceability matrix tooling

## Features

- **pymupdf4llm** extraction with plain PyMuPDF fallback
- **Inline text-image OCR** — detects requirement IDs embedded as raster images and replaces mangled pymupdf4llm output with correct text
- **Header/footer detection** — position-based analysis of repeating text, images, and tables across pages
- **Markdown cleaning** — TOC/list-of-figures removal, heading inference from numbered sections, table repair
- **Whitespace-layout table detection** — span-clustering algorithm for tables without visible borders
- **JSON node extraction** — parses the clean markdown into an ordered list of `title` and `requirement` nodes

## Installation

```bash
cd ReqMap
pip install -r requirements.txt
```

## Usage

### Command line

```bash
# Basic usage — produces <stem>_raw.md and <stem>_clean.md
python -m reqmap path/to/document.pdf

# Also produce <stem>_nodes.json (ordered title + requirement nodes)
python -m reqmap path/to/document.pdf --json

# Specify output directory
python -m reqmap path/to/document.pdf --output-dir ./output

# Disable inline OCR (faster, but misses image-based requirement IDs)
python -m reqmap path/to/document.pdf --no-ocr

# Only produce raw markdown (skip cleaning and JSON)
python -m reqmap path/to/document.pdf --no-clean

# Verbose logging
python -m reqmap path/to/document.pdf -v
```

### Python API

```python
from pathlib import Path
from reqmap.extractor import PDFExtractor
from reqmap.node_parser import parse_nodes, save_nodes

# Step 1 — extract markdown
extractor = PDFExtractor(
    enable_ocr=True,           # OCR inline text-images
    cleaning_config={          # MarkdownCleaner options
        'remove_toc': True,
        'remove_page_numbers': True,
    },
    hf_threshold_pages=3,     # min pages for header/footer detection
    hf_zone_pct=0.10,         # top/bottom 10% zone
)
raw_md, clean_md = extractor.extract(Path("document.pdf"))

# Step 2 — parse into structured nodes
data = parse_nodes(clean_md, source="document.pdf")
save_nodes(data, Path("document_nodes.json"))
```

## Output

### Markdown files

| File | Description |
|---|---|
| `<stem>_raw.md` | pymupdf4llm output after header/footer removal and OCR injection |
| `<stem>_clean.md` | Further cleaned: TOC removed, headings inferred, tables repaired |

### JSON nodes (`--json`)

An ordered list of `title` and `requirement` nodes parsed from the clean markdown.

```json
{
  "source": "document.pdf",
  "node_count": 119,
  "title_count": 58,
  "requirement_count": 61,
  "nodes": [
    {
      "order": 1,
      "type": "title",
      "section": "4",
      "title": "Scope of Work",
      "description": "..."
    },
    {
      "order": 2,
      "type": "title",
      "section": "4.1",
      "title": "Customer undertakings",
      "description": ""
    },
    {
      "order": 3,
      "type": "requirement",
      "req_id": "HAR SSOW-1",
      "title": "Inputs",
      "description": "The Customer is committed to deliver the following inputs:\n..."
    }
  ]
}
```

**Node fields:**

| Field | Applies to | Description |
|---|---|---|
| `order` | both | 1-based sequential position in the document |
| `type` | both | `"title"` or `"requirement"` |
| `section` | title | Section number, e.g. `"4.3.1"` |
| `title` | both | Heading text (titles) or name after `/` (requirements) |
| `req_id` | requirement | Full ID string, e.g. `"HAR SSOW-7"` |
| `description` | both | Body text until the next node; noise lines stripped |

## Pipeline

```
PDF
 └─► pymupdf4llm extraction
      └─► Header/footer removal   (HeaderFooterDetector)
           └─► Inline OCR injection  (InlineImageOCR)
                └─► Markdown cleaning   (MarkdownCleaner)
                     ├─► <stem>_raw.md
                     ├─► <stem>_clean.md
                     └─► <stem>_nodes.json   (NodeParser, --json)
```

## Architecture

```
reqmap/
├── extractor.py               # PDFExtractor — orchestrates the full pipeline
├── inline_image_ocr.py        # InlineImageOCR — detect + OCR small text-images
├── markdown_cleaner.py        # MarkdownCleaner — clean/structure markdown
├── header_footer_detector.py  # HeaderFooterDetector — repeating H/F removal
├── node_parser.py             # parse_nodes — extract ordered title/req nodes
└── cli.py                     # CLI entry point
```

## Dependencies

| Package | Purpose |
|---|---|
| pymupdf | PDF parsing, text/image block extraction |
| pymupdf4llm | High-quality PDF → markdown conversion |
| rapidocr-onnxruntime | OCR engine for inline text-images |
| numpy | Image array handling, statistical analysis |
| Pillow | Image processing |
