# ReqMap

**PDF → Markdown → Structured nodes** for requirement documents, with a web UI to review them.

Takes a PDF as input and produces:
1. A markdown file, converted by a [pdf2md](https://github.com/laurentcarcagno/pdf2md) server (pdf2md-ui, see *Installation*)
2. Optionally, a structured JSON file of ordered title and requirement nodes — ready for traceability matrix tooling

The repo has three layers: the `reqmap/` library (this README), a FastAPI `backend/` and a Next.js `frontend/`
(styled with the THOR · Hemeria design system, see `DESIGN.md`).

## Features

- **pdf2md** multi-pass conversion, done by the pdf2md server: per-page classification, then a fallback chain of engines
  (geometric/pdfplumber, OCR, docling, marker, plain PyMuPDF). ReqMap embeds none of these engines
- **Table handling**, chosen in the upload dialog: *Image* (`--tables-as-images`, the default, see `TABLES_AS_IMAGES`) keeps
  complex tables exactly as laid out in the PDF, *HTML* (`--tables-html`) keeps cell colours and text styles, *Markdown*
  keeps plain text tables; the web app displays all three and the Excel export embeds them as pictures (HTML keeps cell backgrounds, text colour and bold)
- **Requirement IDs drawn as pictures** are OCR'd by pdf2md into image alt text and turned back into text lines
  (`reqmap/pdf_source.py`)
- Header/footer, table-of-contents and figure handling done by pdf2md
- **Customer formats** — `config/customers.json` gives each customer its requirement patterns and, optionally, the
  pdf2md post-processing plugins to run (`post_process`: plugin name → script in `config/plugins/`). `tas` (Thales
  Alénia Space) runs the plugin `Thales Alénia Space`, which marks the `#ID Title … ##` requirements. The scripts are
  registered on the pdf2md server before each conversion, when they changed (see *pdf2md server*)
- **JSON node extraction** — parses the markdown into an ordered list of `title` and `requirement` nodes,
  with customer-specific patterns (`config/customers.json`)

## Installation

```bash
git clone https://github.com/laurentcarcagno/reqmap.git
cd reqmap
pip install -r requirements.txt        # httpx, pydantic, Pillow (the backend has its own requirements)
```

### pdf2md server

PDFs are converted by a [pdf2md-ui](https://gitlab.karka.lan/tools/pdf2md-ui) server (REST API, `/api/v1/jobs`).
Configure it with environment variables (or `backend/.env`, root `.env` for compose):

| Variable | |
|---|---|
| `PDF2MD_URL` | server address, e.g. `https://pdf2md.karka.lan` |
| `PDF2MD_TOKEN` | personal access token `p2m_…` (page *Agents IA (MCP)* of the server) |
| `PDF2MD_CA_BUNDLE` | root certificate of a private CA (backend: mounted from `PDF2MD_CA_FILE`, default the host bundle) |
| `PDF2MD_TIMEOUT` | seconds to wait for a conversion (1800) |
| `PDF2MD_HOST`, `PDF2MD_HOST_IP` | compose only: host name of the server and the address it is mapped to in the container (default `pdf2md.karka.lan` → `host-gateway`, for a server running on the same host: a rootless container cannot reach the host's LAN address) |

**Plugins.** The server runs the post-processing plugins of the account the token belongs to. The plugins ReqMap
needs are versioned here, in `config/plugins/`, and declared by customer in `config/customers.json`. Before each
conversion ReqMap compares them with the server's copy and registers them when they differ (`POST /plugins`, same
name = replaced), then asks for them with `post_process`. A plugin must pass the server's static check (text
processing imports only). To add one: put the script in `config/plugins/` and add it to the customer.

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

`<stem>.md` — the pdf2md server's output (headers/footers and tables of contents removed, figure references dropped,
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
 └─► pdf2md server (job: classify pages → engine fallback chain → plugins → markdown + images)
      └─► inline_id_images         (ID pictures → text lines, other figures dropped)
           ├─► <stem>.md
           └─► parse_nodes ──► <stem>_nodes.json   (--json)
```

## Architecture

```
reqmap/
├── pdf_source.py   # pdf_to_markdown — conversion through the pdf2md server, ID pictures → text
├── pdf2md_client.py # client of the server: jobs, plugin registration
├── node_parser.py  # parse_nodes — extract ordered title/req nodes
└── cli.py          # CLI entry point
config/
├── customers.json  # customer formats
└── plugins/        # pdf2md post-processing plugins (registered on the server)
```

## Dependencies

| Package | Purpose |
|---|---|
| httpx | Client of the pdf2md server |
| pydantic | Settings and schemas |
| Pillow | Tables and figures of the Excel export |

