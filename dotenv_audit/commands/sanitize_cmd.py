"""sanitize_cmd.py – CLI subcommand: dotenv-audit sanitize."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv_audit.parser import parse_env_file
from dotenv_audit.reporter import _colorize
from dotenv_audit.sanitizer import sanitize_env_file
from dotenv_audit.scanner import scan_directory


def cmd_sanitize(args: argparse.Namespace) -> int:
    """Scan *directory* for env files and report sanitization issues.

    Returns 0 when all files are clean, 1 when issues are found,
    2 when the directory does not exist.
    """
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    use_color = not getattr(args, "no_color", False)
    write_back = getattr(args, "write", False)

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.")
        return 0

    any_issues = False
    for path in env_files:
        parsed = parse_env_file(str(path))
        result = sanitize_env_file(parsed)
        if result.has_issues:
            any_issues = True
            header = _colorize(f"[sanitize] {result.source}", "yellow", use_color)
            print(header)
            print(result.summary())
            if write_back:
                Path(result.source).write_text("\n".join(result.clean_lines) + "\n")
                note = _colorize("  -> file rewritten", "green", use_color)
                print(note)
        else:
            ok = _colorize(f"[sanitize] {result.source}: clean", "green", use_color)
            print(ok)

    return 1 if any_issues else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "sanitize",
        help="detect and optionally fix unsafe characters in env values",
    )
    p.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="directory to scan (default: current directory)",
    )
    p.add_argument(
        "--write",
        action="store_true",
        help="rewrite files in-place with sanitized values",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI colour output",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_sanitize(args)
