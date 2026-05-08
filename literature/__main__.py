"""CLI: ``python -m literature search "..."`` or ``python -m literature doi <doi>``."""

from __future__ import annotations

import argparse
import json
import sys

from literature.crossref import (
    CrossrefClient,
    CrossrefError,
    normalize_doi_input,
    work_to_reference_dict,
)


def _dump(obj: object) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> int:
    p = argparse.ArgumentParser(description="Crossref literature lookup (AIITE).")
    p.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout seconds (default: 30)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("search", help="Free-text search Crossref works")
    ps.add_argument("query", help="Search query")
    ps.add_argument("--rows", type=int, default=10, help="Max rows (default 10)")
    ps.add_argument("--offset", type=int, default=0)
    ps.add_argument(
        "--filter",
        dest="filter_expr",
        metavar="EXPR",
        help="Crossref filter, e.g. type:journal-article",
    )
    ps.add_argument("--raw", action="store_true", help="Print raw Crossref JSON envelope")

    pd = sub.add_parser("doi", help="Fetch metadata for one DOI")
    pd.add_argument("doi", help="DOI or https://doi.org/... URL")
    pd.add_argument("--raw", action="store_true", help="Print raw Crossref JSON envelope")

    args = p.parse_args()
    client = CrossrefClient(timeout=args.timeout)

    try:
        if args.cmd == "search":
            if args.raw:
                data = client.search_works(
                    args.query,
                    rows=args.rows,
                    offset=args.offset,
                    filter_expr=args.filter_expr,
                )
                _dump(data)
                return 0
            refs, total = client.references_from_search(
                args.query,
                rows=args.rows,
                offset=args.offset,
                filter_expr=args.filter_expr,
            )
            _dump({"total_results": total, "references": refs})
            return 0

        if args.cmd == "doi":
            doi = normalize_doi_input(args.doi)
            data = client.work_by_doi(doi)
            if args.raw:
                _dump(data)
                return 0
            msg = data.get("message")
            if not isinstance(msg, dict):
                print("Unexpected response: no message", file=sys.stderr)
                return 1
            _dump(work_to_reference_dict(msg, ref_id=1))
            return 0

    except CrossrefError as e:
        print(f"crossref: {e}", file=sys.stderr)
        if e.body:
            print(e.body[:2000], file=sys.stderr)
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
