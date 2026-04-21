#!/usr/bin/env python3
"""Split Chinese text into sentences by punctuation."""

from __future__ import annotations

import argparse
import re
import sys
from typing import Iterable

_END_CHARS = "。！？!?…"
_WEAK_CHARS = "；;\n"

_END_RE = re.compile(rf"([{_END_CHARS}]+[\"」』\)]?)\s*")


def split_sentences(text: str, *, use_weak: bool = False) -> list[str]:
    text = text.strip()
    if not text:
        return []

    pattern = _END_RE
    if use_weak:
        pattern = re.compile(
            rf"([{_END_CHARS}{re.escape(_WEAK_CHARS)}]+[\"」』\)]?)\s*"
        )

    parts: list[str] = []
    start = 0
    for m in pattern.finditer(text):
        end = m.end()
        chunk = text[start:end].strip()
        if chunk:
            parts.append(chunk)
        start = end
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def iter_lines(sentences: Iterable[str]) -> Iterable[str]:
    for s in sentences:
        line = " ".join(s.split())
        if line:
            yield line


def main() -> int:
    p = argparse.ArgumentParser(description="Split Chinese text into sentences.")
    src = p.add_mutually_exclusive_group()
    src.add_argument("text", nargs="?", help="Raw text to split")
    src.add_argument("--file", "-f", metavar="PATH", help="Read text from file (UTF-8)")
    src.add_argument("--stdin", action="store_true", help="Read text from stdin")
    p.add_argument(
        "--weak",
        action="store_true",
        help="Also split on semicolons and newlines",
    )
    p.add_argument("-o", "--output", metavar="PATH", help="Write lines to file (UTF-8)")
    args = p.parse_args()

    if args.stdin:
        raw = sys.stdin.read()
    elif args.file:
        with open(args.file, encoding="utf-8") as fh:
            raw = fh.read()
    elif args.text is not None:
        raw = args.text
    else:
        p.print_help()
        return 2

    sents = split_sentences(raw, use_weak=args.weak)
    lines = list(iter_lines(sents))
    out = "\n".join(lines) + ("\n" if lines else "")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
