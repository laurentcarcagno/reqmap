"""Parse clean markdown into an ordered list of title and requirement nodes.

A **title** node is a numbered section heading (e.g. ``## **4.3.1 Design**``).
A **requirement** node starts with a requirement ID line
(e.g. ``HAR SSOW-7 / Electrical detail design``).

Each node accumulates the body text that follows it until the next node is
detected.  Noise lines (page markers, watermarks, non-semantic headings) are
stripped from descriptions.
"""

import json
import re
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Numbered heading:  ## **4.3.1 Design**  or  ## 4 Scope of Work
_TITLE_RE = re.compile(
    r'^\s*#{1,6}\s+\*?\*?'           # markdown heading + optional bold
    r'(\d+(?:\.\d+)*)'               # section number  (group 1)
    r'\s+'                            # separator
    r'(.*?)'                          # heading text   (group 2)
    r'\*?\*?\s*$',                    # optional closing bold
    re.IGNORECASE,
)

# Requirement ID line:  HAR SSOW-7 / Electrical detail design
_REQ_RE = re.compile(
    r'^(HAR\s+SSOW-\d+)\s*/\s*(.+)$',
    re.IGNORECASE,
)

# Noise lines to discard completely (never added to descriptions)
_NOISE_PATTERNS: List[re.Pattern] = [
    re.compile(r'^\s*Airbus\s+Amber\s*$', re.IGNORECASE),
    re.compile(r'^\s*unclassified\s*$', re.IGNORECASE),
    re.compile(r'^\s*AIRBUS\s*$', re.IGNORECASE),
    # Page-reference lines like "OGM-SOW-ADSF-21001104007 Version: 2 Date: ... Page N"
    re.compile(r'OGM-SOW-ADSF.*?Page\s+\d+', re.IGNORECASE),
    # Non-numbered markdown headings that are document artefacts
    re.compile(r'^\s*#{1,6}\s+\*?\*?(?:AIRBUS|Harness\s+SOW|Airbus\s+Amber|'
               r'Remarks?:|Notes?:|None\.|unclassified)\*?\*?\s*$',
               re.IGNORECASE),
    # Standalone bold artefact lines (not headings)
    re.compile(r'^\s*\*\*Harness\s+SOW\*\*\s*$', re.IGNORECASE),
    # Picture placeholders
    re.compile(r'^\s*\*\*==>.*?<==\*\*\s*$'),
    re.compile(r'^\s*\*\*-{5}\s+(?:Start|End)\s+of\s+picture\s+text\s+-{5}\*\*'),
    # End-of-document markers
    re.compile(r'^#+\s+\*?\*?End\s+of\s+Document\*?\*?\s*$', re.IGNORECASE),
]


def _is_noise(line: str) -> bool:
    return any(p.search(line) for p in _NOISE_PATTERNS)


def _clean_title_text(text: str) -> str:
    """Strip markdown bold markers and extra whitespace."""
    text = re.sub(r'\*+', '', text)
    return text.strip()


def _flush_description(lines: List[str]) -> str:
    """Join accumulated description lines, stripping leading/trailing blanks
    and collapsing internal runs of more than two blank lines."""
    # Strip italic/bold markers from the start of lines for cleaner text
    result_lines: List[str] = []
    for ln in lines:
        # Remove leading/trailing markdown italic/bold markers
        clean = re.sub(r'^[\s_*]+', '', ln)
        clean = re.sub(r'[\s_*]+$', '', clean)
        result_lines.append(clean)

    text = '\n'.join(result_lines)
    # Collapse 3+ consecutive blank lines → 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_nodes(clean_md: str, source: str = "") -> dict:
    """Parse *clean_md* and return a JSON-serialisable dict.

    Args:
        clean_md: Content of the cleaned markdown file.
        source:   Original PDF filename (stored in output for reference).

    Returns:
        ``{"source": ..., "nodes": [...]}``
    """
    nodes: List[dict] = []
    order = 0
    seen_req_ids: set = set()

    # Current node being built
    cur_node: Optional[dict] = None
    desc_lines: List[str] = []

    def _commit():
        nonlocal cur_node, desc_lines
        if cur_node is not None:
            cur_node["description"] = _flush_description(desc_lines)
            nodes.append(cur_node)
        cur_node = None
        desc_lines = []

    for raw_line in clean_md.splitlines():
        line = raw_line.rstrip()

        # --- Skip noise lines entirely ---
        if _is_noise(line):
            continue

        # --- Try title match ---
        m_title = _TITLE_RE.match(line)
        if m_title:
            _commit()
            order += 1
            section = m_title.group(1)
            title_text = _clean_title_text(m_title.group(2))
            cur_node = {
                "order": order,
                "type": "title",
                "section": section,
                "title": title_text,
                "description": "",
            }
            desc_lines = []
            continue

        # --- Try requirement match ---
        m_req = _REQ_RE.match(line)
        if m_req:
            req_id = re.sub(r'\s+', ' ', m_req.group(1)).strip()
            if req_id in seen_req_ids:
                # Duplicate — treat rest of lines as noise until next node
                _commit()
                continue
            seen_req_ids.add(req_id)
            _commit()
            order += 1
            req_title = m_req.group(2).strip()
            cur_node = {
                "order": order,
                "type": "requirement",
                "req_id": req_id,
                "title": req_title,
                "description": "",
            }
            desc_lines = []
            continue

        # --- Accumulate description ---
        if cur_node is not None:
            desc_lines.append(line)

    # Flush the last node
    _commit()

    return {
        "source": source,
        "node_count": len(nodes),
        "title_count": sum(1 for n in nodes if n["type"] == "title"),
        "requirement_count": sum(1 for n in nodes if n["type"] == "requirement"),
        "nodes": nodes,
    }


def parse_nodes_from_file(clean_md_path: Path) -> dict:
    """Convenience wrapper that reads *clean_md_path* and calls :func:`parse_nodes`."""
    text = Path(clean_md_path).read_text(encoding="utf-8")
    return parse_nodes(text, source=Path(clean_md_path).name)


def save_nodes(data: dict, output_path: Path) -> None:
    """Serialise *data* to *output_path* as indented JSON (UTF-8)."""
    Path(output_path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
