"""CLI command: sort keys in .env files."""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.sorter import sort_env_file, rewrite_sorted


def _parse_env_file(path: str) -> ParsedEnvFile:
    """Minimal inline parse so sort_cmd has no circular imports."""
    from dotenv_audit.parser import parse_env_file  # local import avoids cycles
    return parse_env_file(path)


def cmd_sort(
    directory: str,
    write: bool = False,
    reverse: bool = False,
    group_comments: bool = False,
    no_color: bool = False,
) -> int:
    if not os.path.isdir(directory):
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.")
        return 0

    any_changed = False
    for path in env_files:
        try:
            parsed = _parse_env_file(path)
        except Exception as exc:  # pragma: no cover
            print(f"warning: could not parse {path}: {exc}", file=sys.stderr)
            continue

        result = sort_env_file(parsed, group_comments=group_comments, reverse=reverse)
        print(str(result))

        if result.changed:
            any_changed = True
            if write:
                lines = rewrite_sorted(parsed, result)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(lines) + "\n")
                print(f"  wrote {path}")

    return 1 if (any_changed and not write) else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("sort", help="sort keys in .env files alphabetically")
    p.add_argument("directory", nargs="?", default=".", help="directory to scan")
    p.add_argument(
        "--write", action="store_true", default=False,
        help="write sorted files in place",
    )
    p.add_argument(
        "--reverse", action="store_true", default=False,
        help="sort in descending order",
    )
    p.add_argument(
        "--group-comments", action="store_true", default=False,
        help="group entries by inline comment prefix before sorting",
    )
    p.add_argument("--no-color", action="store_true", default=False)
    p.set_defaults(_dispatch=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_sort(
        directory=args.directory,
        write=args.write,
        reverse=args.reverse,
        group_comments=args.group_comments,
        no_color=args.no_color,
    )
