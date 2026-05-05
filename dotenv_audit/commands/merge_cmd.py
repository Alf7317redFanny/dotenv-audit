"""CLI command: merge — combine multiple .env files into one."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from dotenv_audit.merger import merge_env_files
from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.scanner import scan_directory


def cmd_merge(args: argparse.Namespace) -> int:
    """Merge .env files found in *directory* and print the result."""
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    env_paths = scan_directory(directory)
    if not env_paths:
        print("No .env files found.")
        return 0

    parsed_files: List[ParsedEnvFile] = []
    for p in sorted(env_paths):
        try:
            pf = ParsedEnvFile.from_file(str(p))
            parsed_files.append(pf)
        except Exception as exc:  # noqa: BLE001
            print(f"warning: could not parse {p}: {exc}", file=sys.stderr)

    result = merge_env_files(parsed_files)

    # Print merged output
    for line in result.to_lines():
        print(line)

    if result.has_conflicts:
        use_color = not getattr(args, "no_color", False)
        prefix = "\033[33m" if use_color else ""
        suffix = "\033[0m" if use_color else ""
        print("", file=sys.stderr)
        print(f"{prefix}Conflicts detected:{suffix}", file=sys.stderr)
        for conflict in result.conflicts:
            print(f"  {conflict}", file=sys.stderr)
        return 1

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "merge",
        help="Merge .env files in a directory into a single output.",
    )
    p.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan for .env files (default: current directory).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable coloured output.",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_merge(args)
