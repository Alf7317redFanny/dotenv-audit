"""CLI command: redact secrets in .env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.redactor import RedactedEnvFile


def cmd_redact(args: argparse.Namespace) -> int:
    """Redact secrets found in .env files under *directory*.

    With ``--in-place`` the original files are overwritten; otherwise the
    redacted content is printed to stdout.
    """
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: '{directory}' is not a directory", file=sys.stderr)
        return 2

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.")
        return 0

    any_redacted = False
    for path in env_files:
        parsed = ParsedEnvFile.from_file(path)
        redacted = RedactedEnvFile.from_parsed(parsed)

        if not redacted.redacted_keys:
            if args.verbose:
                print(f"[clean]  {path}")
            continue

        any_redacted = True
        if args.in_place:
            path.write_text("\n".join(redacted.lines()) + "\n", encoding="utf-8")
            print(f"[redacted] {path} — keys: {', '.join(sorted(redacted.redacted_keys))}")
        else:
            print(f"# --- {path} ---")
            for line in redacted.lines():
                print(line)
            print()

    if any_redacted and not args.in_place:
        return 1  # signal that secrets were found but not written
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "redact",
        help="Redact secret values in .env files",
    )
    p.add_argument("directory", nargs="?", default=".", help="Root directory to scan")
    p.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Overwrite files with redacted content",
    )
    p.add_argument("-v", "--verbose", action="store_true", default=False)
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_redact(args)
