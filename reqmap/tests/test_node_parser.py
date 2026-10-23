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
# Shipped Airbus config: HAR SOW and THW (S2NG-THW-n//R) requirement IDs
# ---------------------------------------------------------------------------

def _airbus_kwargs() -> dict:
    config = json.loads((_ROOT / "config" / "customers.json").read_text(encoding="utf-8"))
    airbus = config["customers"]["airbus"]
    return {
        "req_id_pattern": airbus["req_id_pattern"],
        "noise_patterns": airbus["noise_patterns"],
    }


_THW_MD = """
## 4.1 General Functional Requirements

S2NG-THW-2252//R

The supplier shall propose and justify a general degradation factor for MLI blankets. This factor
can be based on comparative tests from other projects.

S2NG-THW-109//T,S

The MLI shall withstand a general temperature range.

Note: details to be agreed.

S2NG-THW-2601/GDI-135/A,R Optional title

Description under an ID that has a title.

S2NG-THW-4341//

ID whose verification letters were lost at extraction.

## 4.2 MLI performance

S2NG-THW-851//S

Last requirement of the document.

End of Document

S2NG-THW-851 ....................... 4.2 S2NG-THW-2629

S2NG-THW-109 ....................... 4.2 S2NG-THW-894 ....................... 4.3
"""


def test_airbus_config_extracts_thw_requirements():
    result = parse_nodes(_THW_MD, source="thw.md", **_airbus_kwargs())
    reqs = [n for n in result["nodes"] if n["type"] == "requirement"]

    assert [r["req_id"] for r in reqs] == [
        "S2NG-THW-2252//R",
        "S2NG-THW-109//T,S",
        "S2NG-THW-2601/GDI-135/A,R",
        "S2NG-THW-4341//",
        "S2NG-THW-851//S",
    ]
    assert reqs[0]["title"] == ""
    assert reqs[0]["description"].startswith("The supplier shall propose and justify")
    assert reqs[0]["description"].endswith("other projects.")
    assert "Note: details to be agreed." in reqs[1]["description"]
    assert reqs[2]["title"] == "Optional title"
    assert reqs[2]["description"] == "Description under an ID that has a title."


def test_airbus_config_thw_description_stops_at_next_title_and_drops_trailer():
    result = parse_nodes(_THW_MD, source="thw.md", **_airbus_kwargs())
    nodes = result["nodes"]

    assert [n["section"] for n in nodes if n["type"] == "title"] == ["4.1", "4.2"]
    assert nodes[-1]["description"] == "Last requirement of the document."


def test_airbus_config_still_extracts_har_sow_requirements():
    md = "HAR SSOW-7 / Electrical detail design\n\nSome description.\n\nHAR SSOW-8\n\nA reference.\n"
    result = parse_nodes(md, source="har.md", **_airbus_kwargs())
    reqs = [n for n in result["nodes"] if n["type"] == "requirement"]

    assert len(reqs) == 1
    assert reqs[0]["req_id"] == "HAR SSOW-7"
    assert reqs[0]["title"] == "Electrical detail design"
    assert "HAR SSOW-8" in reqs[0]["description"]


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
