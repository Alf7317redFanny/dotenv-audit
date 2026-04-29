"""CLI command: redact — print .env files with secret values masked."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv_audit.parser import parse_env_file
from dotenv_audit.redactor import redact_file
from dotenv_audit.scanner import scan_directory


def cmd_redact(args: argparse.Namespace) -> int:
    """Scan directory and print redacted versions of all .env files."""
    root = Path(args.directory).resolve()
    if not root.exists():
        print(f"error: directory not found: {root}", file=sys.stderr)
        return 2

    env_files = scan_directory(root)
    if not env_files:
        print("No .env files found.")
        return 0

    any_redacted = False
    for path in env_files:
        parsed = parse_env_file(str(path))
        redacted = redact_file(parsed)

        print(f"\n# {path.relative_to(root)}")
        for line in redacted.lines():
            print(line)

        masked = redacted.redacted_keys()
        if masked:
            any_redacted = True
            print(f"# ^ {len(masked)} secret(s) redacted: {', '.join(masked)}")

    return 1 if any_redacted else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "redact",
        help="Print .env files with secret values masked.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_redact(args)
