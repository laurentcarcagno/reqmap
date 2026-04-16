"""ReqMap CLI — extract clean markdown from a PDF.

Usage:
    python -m reqmap input.pdf
    python -m reqmap input.pdf --output-dir ./out
    python -m reqmap input.pdf --no-ocr --no-clean
    python -m reqmap input.pdf --json
"""

import argparse
import logging
import sys
from pathlib import Path

from reqmap.extractor import PDFExtractor
from reqmap.node_parser import parse_nodes, save_nodes


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
        help="Disable inline text-image OCR",
    )
    parser.add_argument(
        "--no-clean", action="store_true",
        help="Skip markdown cleaning (only produce _raw.md)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Parse clean markdown and produce <stem>_nodes.json",
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
    extractor = PDFExtractor(enable_ocr=not args.no_ocr)
    raw_md, clean_md = extractor.extract(pdf_path)

    # Save raw
    raw_path = out_dir / f"{stem}_raw.md"
    raw_path.write_text(raw_md, encoding="utf-8")
    print(f"Raw markdown  → {raw_path}  ({len(raw_md):,} chars)")

    # Save clean
    if not args.no_clean:
        clean_path = out_dir / f"{stem}_clean.md"
        clean_path.write_text(clean_md, encoding="utf-8")
        print(f"Clean markdown → {clean_path}  ({len(clean_md):,} chars)")

    # Save JSON nodes
    if args.json and not args.no_clean:
        json_path = out_dir / f"{stem}_nodes.json"
        data = parse_nodes(clean_md, source=pdf_path.name)
        save_nodes(data, json_path)
        print(
            f"JSON nodes     → {json_path}  "
            f"({data['node_count']} nodes: "
            f"{data['title_count']} titles, "
            f"{data['requirement_count']} requirements)"
        )


if __name__ == "__main__":
    main()
