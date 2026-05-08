"""Crossref REST API client for literature lookup and indexing.

Docs: https://api.crossref.org/swagger-ui/index.html
Etiquette: https://github.com/CrossRef/rest-api-doc#good-manners--more-reliable-service

Set ``CROSSREF_MAILTO`` to a contact email so User-Agent includes ``mailto:`` (recommended).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_BASE = "https://api.crossref.org"


class CrossrefError(Exception):
    """Crossref HTTP or parse failure."""

    def __init__(self, message: str, *, status: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


def _mailto_from_env() -> str | None:
    raw = (os.environ.get("CROSSREF_MAILTO") or "").strip()
    return raw or None


def _user_agent() -> str:
    mailto = _mailto_from_env()
    base = "AIITE-literature/1.0 (+https://github.com/WD-GIF/AIITE)"
    if mailto:
        return f"{base} (mailto:{mailto})"
    return f"{base} (mailto:not-configured; set CROSSREF_MAILTO)"


def _request_json(url: str, *, timeout: float = 30.0) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": _user_agent(),
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise CrossrefError(
            f"Crossref HTTP {e.code}: {e.reason}",
            status=e.code,
            body=body,
        ) from e
    except urllib.error.URLError as e:
        raise CrossrefError(f"Crossref network error: {e.reason!s}") from e

    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as e:
        raise CrossrefError(f"Invalid JSON from Crossref: {e}") from e
    return data


def _first_title(work: dict[str, Any]) -> str:
    titles = work.get("title")
    if isinstance(titles, list) and titles:
        return str(titles[0]).strip()
    if isinstance(titles, str):
        return titles.strip()
    return ""


def _format_author(entry: dict[str, Any]) -> str:
    given = str(entry.get("given") or "").strip()
    family = str(entry.get("family") or "").strip()
    parts = [p for p in (given, family) if p]
    return " ".join(parts) if parts else ""


def _authors(work: dict[str, Any]) -> list[str]:
    authors = work.get("author")
    if not isinstance(authors, list):
        return []
    out: list[str] = []
    for a in authors:
        if isinstance(a, dict):
            s = _format_author(a)
            if s:
                out.append(s)
    return out


def _year(work: dict[str, Any]) -> int | None:
    issued = work.get("issued") or work.get("published-print") or work.get("published-online")
    if not isinstance(issued, dict):
        return None
    parts = issued.get("date-parts")
    if not isinstance(parts, list) or not parts:
        return None
    first = parts[0]
    if not isinstance(first, list) or not first:
        return None
    try:
        y = int(first[0])
        return y if y > 1000 else None
    except (TypeError, ValueError):
        return None


def _venue(work: dict[str, Any]) -> str | None:
    for key in ("container-title", "short-container-title", "publisher"):
        val = work.get(key)
        if isinstance(val, list) and val:
            s = str(val[0]).strip()
            if s:
                return s
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _doi_str(work: dict[str, Any]) -> str | None:
    d = work.get("DOI")
    if isinstance(d, str) and d.strip():
        return d.strip()
    return None


def _landing_url(work: dict[str, Any]) -> str | None:
    """Prefer canonical DOI resolver; avoid picking PDF ``link`` entries as the primary URL."""
    doi = _doi_str(work)
    if doi:
        return f"https://doi.org/{urllib.parse.quote(doi, safe=':/')}"

    html_urls: list[str] = []
    other_urls: list[str] = []
    for link in work.get("link") or []:
        if not isinstance(link, dict):
            continue
        u = link.get("URL")
        if not isinstance(u, str) or not u.startswith("http"):
            continue
        ct = str(link.get("content-type") or "").lower()
        if "text/html" in ct:
            html_urls.append(u)
        else:
            other_urls.append(u)

    if html_urls:
        return html_urls[0]

    url = work.get("URL")
    if isinstance(url, str) and url.startswith("http"):
        return url

    if other_urls:
        return other_urls[0]
    return None


def work_to_reference_dict(work: dict[str, Any], *, ref_id: int = 0) -> dict[str, Any]:
    """Map a Crossref ``message`` work object to API-shaped ``Reference`` (spec §10.1)."""
    title = _first_title(work)
    authors = _authors(work)
    return {
        "id": ref_id,
        "authors": authors if authors else ["(unknown)"],
        "title": title if title else "(untitled)",
        "year": _year(work),
        "venue": _venue(work),
        "doi": _doi_str(work),
        "url": _landing_url(work),
    }


_DOI_CLEAN_RE = re.compile(r"^https?://(?:dx\.)?doi\.org/", re.I)


def normalize_doi_input(doi_or_url: str) -> str:
    s = doi_or_url.strip()
    s = _DOI_CLEAN_RE.sub("", s).strip()
    return s


@dataclass
class CrossrefClient:
    """Thin synchronous Crossref client (stdlib HTTP only)."""

    base_url: str = DEFAULT_BASE
    timeout: float = 30.0

    def search_works(
        self,
        query: str,
        *,
        rows: int = 20,
        offset: int = 0,
        sort: str | None = "relevance",
        filter_expr: str | None = None,
    ) -> dict[str, Any]:
        """Free-text search via ``GET /works``.

        ``filter_expr`` uses Crossref filter syntax, e.g. ``type:journal-article``.
        """
        query = query.strip()
        if not query:
            raise CrossrefError("Empty search query")

        params: list[tuple[str, str]] = [
            ("query", query),
            ("rows", str(max(1, min(rows, 1000)))),
            ("offset", str(max(0, offset))),
        ]
        if sort:
            params.append(("sort", sort))
        if filter_expr:
            params.append(("filter", filter_expr))

        qs = urllib.parse.urlencode(params)
        url = f"{self.base_url.rstrip('/')}/works?{qs}"
        return _request_json(url, timeout=self.timeout)

    def work_by_doi(self, doi: str) -> dict[str, Any]:
        """Resolve a single DOI via ``GET /works/{doi}``."""
        doi_clean = normalize_doi_input(doi)
        if not doi_clean:
            raise CrossrefError("Empty DOI")

        # Keep slashes unencoded; Crossref accepts readable paths like .../works/10.1145/...
        encoded = urllib.parse.quote(doi_clean, safe="/:.()")
        url = f"{self.base_url.rstrip('/')}/works/{encoded}"
        return _request_json(url, timeout=self.timeout)

    def references_from_search(
        self,
        query: str,
        *,
        rows: int = 10,
        offset: int = 0,
        filter_expr: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return ``Reference``-like dicts plus total result count (if API provides it)."""
        payload = self.search_works(
            query, rows=rows, offset=offset, filter_expr=filter_expr
        )
        msg = payload.get("message")
        if not isinstance(msg, dict):
            raise CrossrefError("Unexpected Crossref response: missing message")

        items = msg.get("items")
        if not isinstance(items, list):
            items = []

        total = msg.get("total-results")
        try:
            total_n = int(total) if total is not None else len(items)
        except (TypeError, ValueError):
            total_n = len(items)

        refs: list[dict[str, Any]] = []
        for i, it in enumerate(items, start=1):
            if isinstance(it, dict):
                refs.append(work_to_reference_dict(it, ref_id=i))

        return refs, total_n
