"""CLI command: dotenv-audit score — print risk scores for .env files."""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import parse_env_file
from dotenv_audit.scorer import score_many, FileScore


_LEVEL_COLORS = {
    "low": "\033[32m",      # green
    "medium": "\033[33m",   # yellow
    "high": "\033[31m",     # red
    "critical": "\033[35m", # magenta
}
_RESET = "\033[0m"


def _fmt(fs: FileScore, color: bool) -> str:
    prefix = _LEVEL_COLORS.get(fs.level, "") if color else ""
    reset = _RESET if color else ""
    return (
        f"{prefix}[{fs.level.upper():8s}]{reset} "
        f"score={fs.score:3d}  "
        f"secrets={fs.secret_count}  "
        f"lint={fs.lint_issue_count}  "
        f"empty={fs.empty_value_count}  "
        f"{fs.path}"
    )


def cmd_score(args: argparse.Namespace) -> int:
    directory = args.directory
    if not os.path.isdir(directory):
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    paths = scan_directory(directory)
    if not paths:
        print("No .env files found.")
        return 0

    parsed = [parse_env_file(p) for p in paths]
    scores = score_many(parsed)

    use_color = sys.stdout.isatty() and not args.no_color
    for fs in scores:
        print(_fmt(fs, use_color))

    worst = scores[0].level if scores else "low"
    if worst in ("high", "critical"):
        return 1
    return 0


def register(subparsers) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "score",
        help="Print a risk score for each discovered .env file",
    )
    p.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_score(args)
