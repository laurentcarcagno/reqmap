"""Client of the pdf2md server (pdf2md-ui): PDF conversion and post-processing plugins.

The server converts the PDF and runs the post-processing plugins of the account the access token
belongs to. The plugins ReqMap needs live in this repository (``config/plugins``): they are
registered on the server before a conversion, only when they differ from what it already has.
"""

from __future__ import annotations

import io
import json
import os
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

import httpx

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_POLL_SECONDS = 2.0


class Pdf2mdError(RuntimeError):
    """The pdf2md server refused or failed a request."""


@dataclass(frozen=True)
class Pdf2mdServer:
    """Where the pdf2md server is and how to log in (a personal access token ``p2m_...``)."""

    url: str
    token: str
    ca_bundle: Optional[str] = None
    timeout: float = 1800.0

    @classmethod
    def from_env(cls) -> "Pdf2mdServer":
        """Read PDF2MD_URL, PDF2MD_TOKEN, PDF2MD_CA_BUNDLE and PDF2MD_TIMEOUT."""
        return cls(
            url=os.environ.get("PDF2MD_URL", ""),
            token=os.environ.get("PDF2MD_TOKEN", ""),
            ca_bundle=os.environ.get("PDF2MD_CA_BUNDLE") or None,
            timeout=float(os.environ.get("PDF2MD_TIMEOUT") or 1800),
        )

    def client(self) -> httpx.Client:
        if not self.url or not self.token:
            raise Pdf2mdError("pdf2md server not configured: set PDF2MD_URL and PDF2MD_TOKEN")
        return httpx.Client(
            base_url=self.url.rstrip("/") + "/api/v1",
            headers={"Authorization": f"Bearer {self.token}"},
            verify=self.ca_bundle or True,
            timeout=60.0,
        )


def _check(reply: httpx.Response, what: str) -> httpx.Response:
    if reply.is_success:
        return reply
    try:
        detail = reply.json().get("error") or reply.json().get("detail")
    except ValueError:
        detail = reply.text[:200]
    raise Pdf2mdError(f"pdf2md server: {what} failed ({reply.status_code}): {detail}")


def sync_plugins(client: httpx.Client, post_process: Mapping[str, str]) -> None:
    """Register the plugins on the server, replacing those whose script changed.

    ``post_process`` maps a plugin name to its script, relative to the repository root. The
    plugins of the server are per account: a plugin of the account with the same name is replaced.
    """
    for name, script in post_process.items():
        path = (_PROJECT_ROOT / script).resolve()
        if not path.is_relative_to(_PROJECT_ROOT):
            raise ValueError(f"plugin script outside the repository: {script}")
        source = path.read_text(encoding="utf-8")
        current = client.get("/plugins/source", params={"name": name})
        if current.status_code == 200 and current.text == source:
            continue
        _check(client.post("/plugins", json={"name": name, "source": source}), f"plugin '{name}'")


def convert(
    server: Pdf2mdServer,
    pdf_path: Path,
    *,
    ocr: bool = True,
    tables: str = "markdown",
    tables_min_rows: int = 1,
    post_process: Optional[Mapping[str, str]] = None,
) -> tuple[str, dict[str, bytes]]:
    """Convert a PDF on the server; return its Markdown and its files by name (images).

    ``tables`` is ``markdown``, ``html`` or ``images`` (pdf2md ``--tables-...``).
    """
    options = {
        "ocr": ocr,
        "tables": tables,
        "tables_min_rows": tables_min_rows,
        "json_mapping": False,
        "post_process": list(post_process or {}),
    }
    with server.client() as client:
        if post_process:
            sync_plugins(client, post_process)
        with pdf_path.open("rb") as handle:
            created = _check(
                client.post(
                    "/jobs",
                    files={"files": (pdf_path.name, handle, "application/pdf")},
                    data={"options": json.dumps(options)},
                    timeout=server.timeout,
                ),
                "upload",
            ).json()
        job_id = created[0]["id"]
        try:
            _wait(client, job_id, server.timeout)
            archive = _check(client.get(f"/jobs/{job_id}/download", timeout=server.timeout), "download")
        finally:
            client.delete(f"/jobs/{job_id}")
    return _read_archive(archive.content)


def _wait(client: httpx.Client, job_id: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while True:
        job = _check(client.get(f"/jobs/{job_id}"), "status").json()
        if job["status"] == "succeeded":
            return
        if job["status"] in ("failed", "canceled"):
            raise Pdf2mdError(f"pdf2md conversion {job['status']}: {job.get('error') or ''}".strip())
        if time.monotonic() > deadline:
            client.post(f"/jobs/{job_id}/cancel")
            raise Pdf2mdError("pdf2md conversion timed out")
        time.sleep(_POLL_SECONDS)


def _read_archive(content: bytes) -> tuple[str, dict[str, bytes]]:
    """The Markdown and the other files of the zip of a job (``<stem>/...``)."""
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = [n for n in archive.namelist() if not n.endswith("/")]
        markdown = next((n for n in sorted(names) if n.endswith(".md")), None)
        if markdown is None:
            raise Pdf2mdError("pdf2md server returned no Markdown")
        files = {Path(n).name: archive.read(n) for n in names if n != markdown}
        return archive.read(markdown).decode("utf-8"), files
