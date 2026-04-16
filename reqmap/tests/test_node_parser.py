"""Regression and unit tests for reqmap.node_parser.

The regression test verifies that parse_nodes() with default (no) arguments
produces output identical to the reference file already committed in output/.
"""

import json
from pathlib import Path

import pytest

from reqmap.node_parser import parse_nodes, parse_nodes_from_file

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parents[2]
_CLEAN_MD = _ROOT / "output" / "AD01_OGM-SOW-ADSF-21001104007_2_OGM_HAR_SOW_clean.md"
_REF_JSON = _ROOT / "output" / "AD01_OGM-SOW-ADSF-21001104007_2_OGM_HAR_SOW_nodes.json"


# ---------------------------------------------------------------------------
# Regression: default call matches committed reference output
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _CLEAN_MD.exists(), reason="Reference clean.md not present")
def test_default_output_matches_reference():
    clean_md = _CLEAN_MD.read_text(encoding="utf-8")
    result = parse_nodes(clean_md, source=_CLEAN_MD.name)
    reference = json.loads(_REF_JSON.read_text(encoding="utf-8"))

    assert result["node_count"] == reference["node_count"]
    assert result["title_count"] == reference["title_count"]
    assert result["requirement_count"] == reference["requirement_count"]

    for i, (got, exp) in enumerate(zip(result["nodes"], reference["nodes"])):
        assert got["order"] == exp["order"], f"Node {i}: order mismatch"
        assert got["type"] == exp["type"], f"Node {i}: type mismatch"
        assert got.get("req_id") == exp.get("req_id"), f"Node {i}: req_id mismatch"
        assert got["title"] == exp["title"], f"Node {i}: title mismatch"


# ---------------------------------------------------------------------------
# Custom patterns work correctly
# ---------------------------------------------------------------------------

_CUSTOM_MD = """
## 1 Introduction

Some intro text.

## 1.1 Scope

Scope text here.

ACME-REQ-001 / First requirement

This is the description.

ACME-REQ-002 / Second requirement

More description.
"""

_CUSTOM_REQ_PATTERN = r"^(ACME-REQ-\d+)\s*/\s*(.+)$"


def test_custom_req_pattern_matches_nodes():
    result = parse_nodes(
        _CUSTOM_MD,
        source="custom_test.md",
        req_id_pattern=_CUSTOM_REQ_PATTERN,
        noise_patterns=[],
    )
    req_nodes = [n for n in result["nodes"] if n["type"] == "requirement"]
    assert len(req_nodes) == 2
    assert req_nodes[0]["req_id"] == "ACME-REQ-001"
    assert req_nodes[0]["title"] == "First requirement"
    assert req_nodes[1]["req_id"] == "ACME-REQ-002"


def test_custom_pattern_title_nodes():
    result = parse_nodes(
        _CUSTOM_MD,
        source="custom_test.md",
        req_id_pattern=_CUSTOM_REQ_PATTERN,
        noise_patterns=[],
    )
    title_nodes = [n for n in result["nodes"] if n["type"] == "title"]
    assert len(title_nodes) == 2
    assert title_nodes[0]["section"] == "1"
    assert title_nodes[1]["section"] == "1.1"


def test_noise_patterns_filter_lines():
    md = "## 1 Section\n\nGOOD LINE\n\nDROP THIS LINE\n\nAnother good line.\n"
    result = parse_nodes(
        md,
        source="noise_test.md",
        req_id_pattern=r"^(NONE-\d+)\s*/\s*(.+)$",
        noise_patterns=[r"^DROP THIS LINE$"],
    )
    title_nodes = [n for n in result["nodes"] if n["type"] == "title"]
    assert len(title_nodes) == 1
    assert "DROP THIS LINE" not in title_nodes[0]["description"]


# ---------------------------------------------------------------------------
# Backward compatibility: no-arg call still works
# ---------------------------------------------------------------------------

def test_no_args_parses_empty_string():
    result = parse_nodes("")
    assert result["node_count"] == 0
    assert result["nodes"] == []


def test_no_args_airbus_req_matched():
    md = "HAR SSOW-1 / My requirement\n\nSome description.\n"
    result = parse_nodes(md)
    assert result["requirement_count"] == 1
    assert result["nodes"][0]["req_id"] == "HAR SSOW-1"
