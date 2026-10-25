"""Tests for the pdf2md image post-processing."""

import io
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from reqmap.pdf2md_client import Pdf2mdError, Pdf2mdServer
from reqmap.pdf_source import inline_id_images, pdf_to_markdown


ID_PATTERN = r"^(HAR\s+SSOW-\d+)\s*/\s*(.+)$"
MARKDOWN = "\n".join([
    "Intro",
    "![HAR SSOW-2 / Input-events](out/p0015_02.png)",
    "![Figure 1: Layout](out/p0015_03.png)",
    "![Gone](out/missing.png)",
    "Outro",
])


def test_id_pictures_become_text_and_figures_are_dropped_without_a_store():
    assert inline_id_images(MARKDOWN, ID_PATTERN) == "Intro\nHAR SSOW-2 / Input-events\nOutro"


def test_figures_are_kept_when_stored(tmp_path: Path):
    (tmp_path / "p0015_03.png").write_bytes(b"png")
    result = inline_id_images(MARKDOWN, ID_PATTERN, tmp_path, "/api/v1/documents/d/assets")
    assert result.splitlines() == [
        "Intro",
        "HAR SSOW-2 / Input-events",
        "![Figure 1: Layout](/api/v1/documents/d/assets/p0015_03.png)",
        "Outro",
    ]


SERVER = Pdf2mdServer("https://pdf2md.test", "p2m_secret")


class FakePdf2md:
    """Just enough of the pdf2md-ui API: plugins, jobs, download."""

    def __init__(self, markdown: str, files: dict[str, bytes] | None = None, status: str = "succeeded"):
        self.markdown, self.files, self.status = markdown, files or {}, status
        self.plugins: dict[str, str] = {}
        self.jobs: list[dict] = []
        self.deleted: list[str] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer p2m_secret"
        path = request.url.path.removeprefix("/api/v1")
        if path == "/plugins/source":
            source = self.plugins.get(request.url.params["name"])
            return httpx.Response(200, text=source) if source is not None else httpx.Response(404)
        if path == "/plugins":
            body = json.loads(request.content)
            self.plugins[body["name"]] = body["source"]
            return httpx.Response(201, json={})
        if path == "/jobs" and request.method == "POST":
            form = request.content.split(b'name="options"')[1].split(b"\r\n\r\n")[1].split(b"\r\n")[0]
            self.jobs.append(json.loads(form))
            return httpx.Response(201, json=[{"id": "job1"}])
        if path == "/jobs/job1" and request.method == "GET":
            return httpx.Response(200, json={"status": self.status, "error": "boom"})
        if path == "/jobs/job1/download":
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("doc/doc.md", self.markdown)
                for name, content in self.files.items():
                    archive.writestr(f"doc/assets/{name}", content)
            return httpx.Response(200, content=buffer.getvalue())
        if path == "/jobs/job1" and request.method == "DELETE":
            self.deleted.append("job1")
            return httpx.Response(204)
        return httpx.Response(404)


@pytest.fixture
def pdf2md(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    def install(fake: FakePdf2md) -> FakePdf2md:
        def client(self: Pdf2mdServer) -> httpx.Client:
            return httpx.Client(base_url="https://pdf2md.test/api/v1", transport=httpx.MockTransport(fake.handle),
                                headers={"Authorization": "Bearer " + self.token})

        monkeypatch.setattr(Pdf2mdServer, "client", client)
        monkeypatch.setattr("reqmap.pdf2md_client._POLL_SECONDS", 0)
        return fake

    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4")
    return install


def test_pdf_is_converted_by_the_server_and_its_figures_are_kept(pdf2md, tmp_path: Path):
    fake = pdf2md(FakePdf2md("Intro\n![Figure 1](assets/p0001_01.png)\n", {"p0001_01.png": b"png", "other.png": b"x"}))
    images = tmp_path / "assets"
    markdown = pdf_to_markdown(tmp_path / "doc.pdf", images_dir=images, asset_url_prefix="/a",
                               tables_as_images=2, server=SERVER)
    assert markdown.splitlines() == ["Intro", "![Figure 1](/a/p0001_01.png)"]
    assert [p.name for p in images.iterdir()] == ["p0001_01.png"]  # only what the Markdown refers to
    assert fake.jobs[0]["tables"] == "images" and fake.jobs[0]["tables_min_rows"] == 2
    assert fake.jobs[0]["json_mapping"] is False
    assert fake.deleted == ["job1"]


def test_table_modes_are_passed_to_the_server(pdf2md, tmp_path: Path):
    fake = pdf2md(FakePdf2md("x"))
    pdf_to_markdown(tmp_path / "doc.pdf", tables_html=True, server=SERVER)
    pdf_to_markdown(tmp_path / "doc.pdf", enable_ocr=False, server=SERVER)
    assert [(j["tables"], j["ocr"]) for j in fake.jobs] == [("html", True), ("markdown", False)]


def test_a_failed_conversion_raises(pdf2md, tmp_path: Path):
    pdf2md(FakePdf2md("x", status="failed"))
    with pytest.raises(Pdf2mdError, match="failed: boom"):
        pdf_to_markdown(tmp_path / "doc.pdf", server=SERVER)


def test_the_server_must_be_configured(tmp_path: Path):
    with pytest.raises(Pdf2mdError, match="PDF2MD_URL"):
        pdf_to_markdown(tmp_path / "doc.pdf", server=Pdf2mdServer("", ""))


def test_tables_as_images_needs_a_kept_images_dir(tmp_path: Path):
    with pytest.raises(ValueError, match="images_dir"):
        pdf_to_markdown(tmp_path / "doc.pdf", tables_as_images=1, server=SERVER)


def test_plugins_are_registered_only_when_they_changed(pdf2md, tmp_path: Path):
    fake = pdf2md(FakePdf2md("x"))
    plugins = {"Thales Alénia Space": "config/plugins/thales_alenia_space.py"}
    pdf_to_markdown(tmp_path / "doc.pdf", post_process=plugins, server=SERVER)
    assert fake.jobs[0]["post_process"] == ["Thales Alénia Space"]
    source = fake.plugins["Thales Alénia Space"]
    assert "def process(" in source
    fake.plugins["Thales Alénia Space"] = "stale"  # an old version on the server is replaced
    pdf_to_markdown(tmp_path / "doc.pdf", post_process=plugins, server=SERVER)
    assert fake.plugins["Thales Alénia Space"] == source


def test_plugin_scripts_must_stay_inside_the_repository(pdf2md, tmp_path: Path):
    pdf2md(FakePdf2md("x"))
    with pytest.raises(ValueError, match="outside the repository"):
        pdf_to_markdown(tmp_path / "doc.pdf", post_process={"evil": "../../etc/passwd.py"}, server=SERVER)


TAS_MARKDOWN = """# 3. GENERAL REQUIREMENTS

3.1 ELECTRICAL REQUIREMENTS

#EUR-DCH-000010 Interconnection wiring Parent(s): none Assignment: Verification: [R, I] The harness shall be built as drawn.

3.1.2 Resistance

#EUR-DCH-000020 Continuity Parent(s): none Assignment: Verification: [T] Continuity shall be measured. ##
"""


def _tas_customer() -> dict:
    import json

    config = Path(__file__).resolve().parents[2] / "config" / "customers.json"
    return json.loads(config.read_text(encoding="utf-8"))["customers"]["tas"]


def _tas_customer() -> dict:
    config = Path(__file__).resolve().parents[2] / "config" / "customers.json"
    return json.loads(config.read_text(encoding="utf-8"))["customers"]["tas"]


def _tas_marked(monkeypatch: pytest.MonkeyPatch, markdown: str) -> str:
    """What the server makes of the Markdown: the plugin script of the customer, run as pdf2md would."""
    import importlib.util
    import sys

    monkeypatch.setitem(sys.modules, "pdf2md", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "pdf2md.plugins", SimpleNamespace(PluginContext=object))
    script = Path(__file__).resolve().parents[2] / _tas_customer()["post_process"]["Thales Alénia Space"]
    spec = importlib.util.spec_from_file_location("tas_plugin", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.process(markdown, SimpleNamespace(plugin_name="tas"))


def test_tas_plugin_marks_the_requirements(monkeypatch: pytest.MonkeyPatch):
    marked = _tas_marked(monkeypatch, TAS_MARKDOWN)
    assert '<a id="eur-dch-000010"></a>**EUR-DCH-000010 Interconnection wiring**' in marked
    assert "<!-- end EUR-DCH-000020 -->" in marked


def test_tas_documents_parse_into_titles_and_requirements(monkeypatch: pytest.MonkeyPatch):
    from reqmap.node_parser import parse_nodes

    tas = _tas_customer()
    data = parse_nodes(
        _tas_marked(monkeypatch, TAS_MARKDOWN),
        req_id_pattern=tas["req_id_pattern"],
        title_pattern=tas["title_pattern"],
        noise_patterns=tas["noise_patterns"],
    )
    assert [(n["type"], n.get("section") or n.get("req_id")) for n in data["nodes"]] == [
        ("title", "3"),
        ("title", "3.1"),
        ("requirement", "EUR-DCH-000010"),
        ("title", "3.1.2"),
        ("requirement", "EUR-DCH-000020"),
    ]
    requirement = data["nodes"][2]
    assert requirement["title"] == "Interconnection wiring"
    assert "Verification: [R, I]" in requirement["description"]
    assert "<!--" not in requirement["description"]  # the end marker is noise


def test_airbus_requirements_marked_by_the_ads_plugin_are_still_found():
    from reqmap.node_parser import parse_nodes

    airbus = json.loads((Path(__file__).resolve().parents[2] / "config" / "customers.json").read_text(encoding="utf-8"))["customers"]["airbus"]
    assert airbus["post_process"] == {"ADS": "config/plugins/ads.py"}
    markdown = '# 1 Scope\n\n<a id="har-ssow-2"></a>**HAR SSOW-2 / Input-events**\n\nThe supplier shall do X.\n'
    nodes = parse_nodes(markdown, source="x", req_id_pattern=airbus["req_id_pattern"],
                        noise_patterns=airbus["noise_patterns"])["nodes"]
    assert [(n["type"], n.get("req_id"), n["title"]) for n in nodes][1:] == [("requirement", "HAR SSOW-2", "Input-events")]
