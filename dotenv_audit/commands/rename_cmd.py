"""CLI command: rename a key across all .env files in a directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv_audit.renamer import rename_key_in_directory


def cmd_rename(args: argparse.Namespace) -> int:
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    if args.old_key == args.new_key:
        print("error: old-key and new-key must differ.", file=sys.stderr)
        return 2

    report = rename_key_in_directory(
        directory,
        old_key=args.old_key,
        new_key=args.new_key,
        dry_run=args.dry_run,
    )

    if not report.results:
        print("No .env files found.")
        return 0

    for result in report.results:
        if not args.no_color:
            marker = "\033[32m✔\033[0m" if result.renamed else "\033[33m–\033[0m"
        else:
            marker = "✔" if result.renamed else "–"
        print(f"  {marker}  {result}")

    print()
    print(report.summary)
    if args.dry_run:
        print("(dry-run: no files were modified)")

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "rename",
        help="Rename a key across all .env files in a directory.",
    )
    parser.add_argument(
        "old_key",
        metavar="OLD_KEY",
        help="The existing key name to rename.",
    )
    parser.add_argument(
        "new_key",
        metavar="NEW_KEY",
        help="The replacement key name.",
    )
    parser.add_argument(
        "--directory",
        "-d",
        default=".",
        help="Directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing to disk.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    parser.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_rename(args)
