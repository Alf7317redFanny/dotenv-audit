"""CLI sub-command: export audit results as JSON or CSV."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.comparator import compare_many
from dotenv_audit.exporter import build_export, to_json, to_csv


def cmd_export(args: argparse.Namespace) -> int:
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: '{directory}' is not a directory", file=sys.stderr)
        return 2

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.", file=sys.stderr)
        return 0

    parsed = [ParsedEnvFile.from_path(p) for p in env_files]
    comparisons = compare_many(parsed) if len(parsed) > 1 else []
    export = build_export(parsed, comparisons)

    fmt = getattr(args, "format", "json")
    if fmt == "csv":
        output = to_csv(export)
    else:
        output = to_json(export)

    out_path = getattr(args, "output", None)
    if out_path:
        Path(out_path).write_text(output, encoding="utf-8")
        print(f"Exported to {out_path}")
    else:
        print(output)

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "export",
        help="Export audit results to JSON or CSV",
    )
    p.add_argument("directory", help="Directory to scan")
    p.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_export(args)
