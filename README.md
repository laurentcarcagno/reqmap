# ReqMap

**PDF → Markdown → Structured nodes** for requirement documents, with a web UI to review them.

Takes a PDF as input and produces:
1. A markdown file, converted by [pdf2md](https://github.com/laurentcarcagno/pdf2md) (git submodule in `pdf2md/`)
2. Optionally, a structured JSON file of ordered title and requirement nodes — ready for traceability matrix tooling

The repo has three layers: the `reqmap/` library (this README), a FastAPI `backend/` and a Next.js `frontend/`
(styled with the THOR · Hemeria design system, see `DESIGN.md`).

## Features

- **pdf2md** multi-pass conversion: per-page classification, then a fallback chain of engines
  (geometric/pdfplumber, OCR with Tesseract + RapidOCR, docling, marker, plain PyMuPDF)
- **Table handling**, chosen in the upload dialog: *Image* (`--tables-as-images`, the default, see `TABLES_AS_IMAGES`) keeps
  complex tables exactly as laid out in the PDF, *HTML* (`--tables-html`) keeps cell colours and text styles, *Markdown*
  keeps plain text tables; the web app displays all three and the Excel export embeds them as pictures (HTML keeps cell backgrounds, text colour and bold)
- **Requirement IDs drawn as pictures** are OCR'd by pdf2md into image alt text and turned back into text lines
  (`reqmap/pdf_source.py`)
- Header/footer, table-of-contents and figure handling done by pdf2md
- **Customer formats** — `config/customers.json` gives each customer its requirement patterns and, optionally, the
  pdf2md post-processing plugins to run (`post_process`: plugin name → script). `tas` (Thales Alénia Space) runs the
  pdf2md plugin `--post-process "Thales Alénia Space"`, which marks the `#ID Title … ##` requirements
- **JSON node extraction** — parses the markdown into an ordered list of `title` and `requirement` nodes,
  with customer-specific patterns (`config/customers.json`)

## Installation

```bash
git clone --recurse-submodules https://github.com/laurentcarcagno/reqmap.git
# already cloned?  git submodule update --init
cd reqmap
pip install -r requirements.txt                    # pdf2md core + OCR
sudo apt install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
```

Optional heavy engines (docling, marker; used on pages the geometric pass cannot handle):

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
pip install "docling>=2.140" "marker-pdf>=2.0"
```

The backend container image already includes them (CPU build of torch). For GPU builds see `pdf2md/README.md`.

## Usage

### Command line

```bash
# Basic usage — produces <stem>.md
python -m reqmap path/to/document.pdf

# Also produce <stem>_nodes.json (ordered title + requirement nodes)
python -m reqmap path/to/document.pdf --json

# Specify output directory
python -m reqmap path/to/document.pdf --output-dir ./output

# Disable OCR (faster, but scanned pages and image-based IDs are lost)
python -m reqmap path/to/document.pdf --no-ocr

# Use a customer format of config/customers.json (requirement patterns + pdf2md plugins);
# "tas" = Thales Alénia Space (#ID Title ... ## requirements), default = Airbus
python -m reqmap path/to/document.pdf --customer tas --json

# Keep tables as pictures of the PDF page (optionally: only tables of MIN_ROWS rows or more)
python -m reqmap path/to/document.pdf --tables-as-images [MIN_ROWS]

# Keep tables as HTML (cell colours, text styles)
python -m reqmap path/to/document.pdf --tables-html

# Verbose logging
python -m reqmap path/to/document.pdf -v
```

### Python API

```python
from pathlib import Path
from reqmap.pdf_source import pdf_to_markdown
from reqmap.node_parser import parse_nodes, save_nodes

# Step 1 — PDF to markdown (pdf2md)
md = pdf_to_markdown(Path("document.pdf"), req_id_pattern=r"^(HAR\s+SSOW-\d+)\s*/\s*(.+)$")

# Step 2 — parse into structured nodes
data = parse_nodes(md, source="document.pdf")
save_nodes(data, Path("document_nodes.json"))
```

## Output

### Markdown file

`<stem>.md` — the pdf2md output (headers/footers and tables of contents removed, figure references dropped,
requirement-ID pictures restored as text).

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
 └─► pdf2md.convert_pdf            (classify pages → engine fallback chain → markdown)
      └─► inline_id_images         (ID pictures → text lines, other figures dropped)
           ├─► <stem>.md
           └─► parse_nodes ──► <stem>_nodes.json   (--json)
```

## Architecture

```
reqmap/
├── pdf_source.py   # pdf_to_markdown — wraps the pdf2md submodule
├── node_parser.py  # parse_nodes — extract ordered title/req nodes
└── cli.py          # CLI entry point
pdf2md/             # git submodule: https://github.com/laurentcarcagno/pdf2md (package in pdf2md/src)
```

## Dependencies

Declared by pdf2md (see `pdf2md/README.md` for the rationale of each):

| Package | Purpose |
|---|---|
| pymupdf, pdfplumber | Page classification, rendering, exact line boxes |
| rapidocr, onnxruntime, opencv-python-headless, Tesseract | OCR of scanned pages and picture-drawn IDs |
| ftfy, pydantic, tqdm | Text repair, settings, progress |
| docling, marker-pdf, torch (optional) | Layout/table models for complex pages |
