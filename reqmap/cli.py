"""ReqMap CLI — extract markdown from a PDF (via pdf2md) and parse it into nodes.

Usage:
    python -m reqmap input.pdf
    python -m reqmap input.pdf --output-dir ./out
    python -m reqmap input.pdf --no-ocr
    python -m reqmap input.pdf --json
"""

import argparse
import logging
import sys
from pathlib import Path

from reqmap.node_parser import _DEFAULT_REQ_ID_PATTERN, parse_nodes, save_nodes
from reqmap.pdf_source import pdf_to_markdown


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="reqmap",
        description="Extract structured markdown from PDF documents.",
    )
    parser.add_argument("pdf", type=Path, help="Path to the input PDF file")
    parser.add_argument(
        "--output-dir", "-o", type=Path, default=None,
        help="Output directory (default: same directory as the PDF)",
    )
    parser.add_argument(
        "--no-ocr", action="store_true",
        help="Disable OCR (faster, but scanned pages and image-based IDs are lost)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Parse the markdown and produce <stem>_nodes.json",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable DEBUG logging",
    )

    args = parser.parse_args(argv)

    # Logging setup
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    pdf_path = args.pdf.resolve()
    if not pdf_path.exists():
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = (args.output_dir or pdf_path.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = pdf_path.stem

    # Extract
    md = pdf_to_markdown(pdf_path, _DEFAULT_REQ_ID_PATTERN, enable_ocr=not args.no_ocr)

    md_path = out_dir / f"{stem}.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"Markdown      → {md_path}  ({len(md):,} chars)")

    # Save JSON nodes
    if args.json:
        json_path = out_dir / f"{stem}_nodes.json"
        data = parse_nodes(md, source=pdf_path.name)
        save_nodes(data, json_path)
        print(
            f"JSON nodes     → {json_path}  "
            f"({data['node_count']} nodes: "
            f"{data['title_count']} titles, "
            f"{data['requirement_count']} requirements)"
        )


if __name__ == "__main__":
    main()
