"""CLI command: diff two .env files."""
from __future__ import annotations

import argparse
import sys
from typing import List

from dotenv_audit.differ import diff_env_files
from dotenv_audit.parser import parse_env_file
from dotenv_audit.reporter import _colorize


def cmd_diff(args: argparse.Namespace) -> int:
    """Compare two .env files and print a human-readable diff."""
    left_path: str = args.left
    right_path: str = args.right
    no_color: bool = getattr(args, "no_color", False)

    for path in (left_path, right_path):
        try:
            open(path).close()
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2

    left = parse_env_file(left_path)
    right = parse_env_file(right_path)
    result = diff_env_files(left, right)

    print(f"--- {result.left_path}")
    print(f"+++ {result.right_path}")

    if not result.has_changes:
        msg = "No differences found."
        print(msg if no_color else _colorize(msg, "green"))
        return 0

    kind_color = {
        "added": "green",
        "removed": "red",
        "changed": "yellow",
        "unchanged": None,
    }

    for line in result.lines:
        text = str(line)
        color = kind_color.get(line.kind)
        if color and not no_color:
            text = _colorize(text, color)
        print(text)

    print()
    summary = result.summary
    print(summary if no_color else _colorize(summary, "yellow"))
    return 1


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "diff",
        help="Show line-level differences between two .env files.",
    )
    p.add_argument("left", help="Base .env file.")
    p.add_argument("right", help="Comparison .env file.")
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable coloured output.",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_diff(args)
