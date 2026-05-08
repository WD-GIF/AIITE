#!/usr/bin/env python3
"""Serve the web UI and Crossref API proxy. Listens only on port 4399."""

from __future__ import annotations

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Crossref polite pool: contact email in User-Agent (overridable by env).
os.environ.setdefault("CROSSREF_MAILTO", "2362138153@qq.com")

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"

from literature.crossref import (  # noqa: E402
    CrossrefClient,
    CrossrefError,
    normalize_doi_input,
    work_to_reference_dict,
)

PORT = 4399
MAX_QUERY_LEN = 512
MAX_ROWS = 25


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/crossref/search":
            self._handle_search(parse_qs(parsed.query))
            return
        if parsed.path == "/api/crossref/doi":
            self._handle_doi(parse_qs(parsed.query))
            return
        super().do_GET()

    def _handle_search(self, qs: dict) -> None:
        q = (qs.get("query") or qs.get("q") or [""])[0].strip()
        rows_raw = (qs.get("rows") or ["10"])[0]
        try:
            rows = max(1, min(int(rows_raw), MAX_ROWS))
        except ValueError:
            rows = 10
        if not q or len(q) > MAX_QUERY_LEN:
            self._json(
                400,
                {"error": {"code": "INVALID_INPUT", "message": "无效检索词或超过长度限制"}},
            )
            return
        try:
            client = CrossrefClient(timeout=30.0)
            refs, total = client.references_from_search(q, rows=rows)
            self._json(200, {"total_results": total, "references": refs})
        except CrossrefError as e:
            self._json(502, {"error": {"code": "UPSTREAM_ERROR", "message": str(e)}})

    def _handle_doi(self, qs: dict) -> None:
        doi = (qs.get("doi") or [""])[0].strip()
        if not doi:
            self._json(400, {"error": {"code": "INVALID_INPUT", "message": "请提供 DOI"}})
            return
        if len(doi) > MAX_QUERY_LEN:
            self._json(400, {"error": {"code": "INVALID_INPUT", "message": "DOI 过长"}})
            return
        try:
            client = CrossrefClient(timeout=30.0)
            data = client.work_by_doi(normalize_doi_input(doi))
            msg = data.get("message")
            if not isinstance(msg, dict):
                self._json(
                    502,
                    {"error": {"code": "INVALID_RESPONSE", "message": "Crossref 响应异常"}},
                )
                return
            ref = work_to_reference_dict(msg, ref_id=1)
            self._json(200, {"references": [ref]})
        except CrossrefError as e:
            code = 404 if e.status == 404 else 502
            self._json(
                code,
                {
                    "error": {
                        "code": "NOT_FOUND" if code == 404 else "UPSTREAM_ERROR",
                        "message": str(e),
                    }
                },
            )


def main() -> int:
    if WEB.is_dir() is False:
        print(f"Missing web root: {WEB}", file=sys.stderr)
        return 1
    addr = ("0.0.0.0", PORT)
    httpd = ThreadingHTTPServer(addr, AppHandler)
    print(f"Open http://127.0.0.1:{PORT}/  (serving {WEB})")
    print("Only port 4399 is used. Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
