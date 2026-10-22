"""Parse clean markdown into an ordered list of title and requirement nodes.

A **title** node is a numbered section heading (e.g. ``## **4.3.1 Design**``).
A **requirement** node starts with a requirement ID line
(e.g. ``HAR SSOW-7 / Electrical detail design``).

Each node accumulates the body text that follows it until the next node is
detected.  Noise lines (page markers, watermarks, non-semantic headings) are
stripped from descriptions.

Customer-specific patterns can be passed directly to :func:`parse_nodes`; when
omitted the module-level Airbus defaults are used (backward-compatible).
"""

import json
import re
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Default (Airbus) regex patterns — used when no overrides are supplied
# ---------------------------------------------------------------------------

# Numbered heading:  ## **4.3.1 Design**  or  ## 4 Scope of Work
_DEFAULT_TITLE_PATTERN: str = (
    r'^\s*#{1,6}\s+\*?\*?'           # markdown heading + optional bold
    r'(\d+(?:\.\d+)*)'               # section number  (group 1)
    r'\s+'                            # separator
    r'(.*?)'                          # heading text   (group 2)
    r'\*?\*?\s*$'                     # optional closing bold
)

# Requirement ID line:  HAR SSOW-7 / Electrical detail design
_DEFAULT_REQ_ID_PATTERN: str = r'^(HAR\s+SSOW-\d+)\s*/\s*(.+)$'

# Noise line patterns (Airbus-specific)
_DEFAULT_NOISE_PATTERNS: List[str] = [
    r'^\s*Airbus\s+Amber\s*$',
    r'^\s*unclassified\s*$',
    r'^\s*AIRBUS\s*$',
    r'OGM-SOW-ADSF.*?Page\s+\d+',
    r'^\s*#{1,6}\s+\*?\*?(?:AIRBUS|Harness\s+SOW|Airbus\s+Amber|Remarks?:|Notes?:|None\.|unclassified)\*?\*?\s*$',
    r'^\s*\*\*Harness\s+SOW\*\*\s*$',
    r'^\s*\*\*==>.*?<==\*\*\s*$',
    r'^\s*\*\*-{5}\s+(?:Start|End)\s+of\s+picture\s+text\s+-{5}\*\*',
    r'^#+\s+\*?\*?End\s+of\s+Document\*?\*?\s*$',
]

# Compiled module-level defaults (reused when no overrides supplied)
_TITLE_RE = re.compile(_DEFAULT_TITLE_PATTERN, re.IGNORECASE)
_REQ_RE = re.compile(_DEFAULT_REQ_ID_PATTERN, re.IGNORECASE)
_NOISE_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in _DEFAULT_NOISE_PATTERNS
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compile_noise(patterns: List[str]) -> List[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def _is_noise(line: str, compiled: List[re.Pattern]) -> bool:
    return any(p.search(line) for p in compiled)


def _clean_title_text(text: str) -> str:
    """Strip markdown bold markers and extra whitespace."""
    text = re.sub(r'\*+', '', text)
    return text.strip()


def _flush_description(lines: List[str]) -> str:
    """Join accumulated description lines, stripping leading/trailing blanks
    and collapsing internal runs of more than two blank lines."""
    result_lines: List[str] = []
    for ln in lines:
        clean = re.sub(r'^[\s_*]+', '', ln)
        clean = re.sub(r'[\s_*]+$', '', clean)
        result_lines.append(clean)

    text = '\n'.join(result_lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_nodes(
    clean_md: str,
    source: str = "",
    *,
    req_id_pattern: Optional[str] = None,
    title_pattern: Optional[str] = None,
    noise_patterns: Optional[List[str]] = None,
) -> dict:
    """Parse *clean_md* and return a JSON-serialisable dict.

    Args:
        clean_md:        Content of the cleaned markdown file.
        source:          Original PDF filename (stored in output for reference).
        req_id_pattern:  Regex string for requirement ID lines (group 1 = ID,
                         group 2 = title).  Defaults to the Airbus pattern.
        title_pattern:   Regex string for numbered section headings (group 1 =
                         section number, group 2 = heading text).  Defaults to
                         the standard markdown numbered-heading pattern.
        noise_patterns:  List of regex strings for lines to discard entirely.
                         Defaults to the Airbus noise pattern list.

    Returns:
        ``{"source": ..., "node_count": ..., "title_count": ...,
           "requirement_count": ..., "nodes": [...]}``
    """
    title_re = (
        re.compile(title_pattern, re.IGNORECASE)
        if title_pattern is not None
        else _TITLE_RE
    )
    req_re = (
        re.compile(req_id_pattern, re.IGNORECASE)
        if req_id_pattern is not None
        else _REQ_RE
    )
    noise_compiled = (
        _compile_noise(noise_patterns)
        if noise_patterns is not None
        else _NOISE_PATTERNS
    )

    nodes: List[dict] = []
    order = 0
    seen_req_ids: set = set()

    cur_node: Optional[dict] = None
    desc_lines: List[str] = []

    def _commit() -> None:
        nonlocal cur_node, desc_lines
        if cur_node is not None:
            cur_node["description"] = _flush_description(desc_lines)
            nodes.append(cur_node)
        cur_node = None
        desc_lines = []

    for raw_line in clean_md.splitlines():
        line = raw_line.rstrip()

        if _is_noise(line, noise_compiled):
            continue

        m_title = title_re.match(line)
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

        m_req = req_re.match(line)
        if m_req:
            req_id = re.sub(r'\s+', ' ', m_req.group(1)).strip()
            if req_id in seen_req_ids:
                _commit()
                continue
            seen_req_ids.add(req_id)
            _commit()
            order += 1
            req_title = (m_req.group(2) or "").strip()  # the title group may be optional
            cur_node = {
                "order": order,
                "type": "requirement",
                "req_id": req_id,
                "title": req_title,
                "description": "",
            }
            desc_lines = []
            continue

        if cur_node is not None:
            desc_lines.append(line)

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
