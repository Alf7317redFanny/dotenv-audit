"""CLI command: tag — display semantic tags for keys in .env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.tagger import tag_env_file, TaggedEnvFile
from dotenv_audit.reporter import _colorize


def _parse_env_file(path: str) -> ParsedEnvFile:
    from dotenv_audit.parser import parse_env_file  # local import to mirror other cmds
    return parse_env_file(path)


def _print_tagged(tagged: TaggedEnvFile, *, color: bool) -> None:
    header = _colorize(f"\n=== {tagged.source} ===", "cyan") if color else f"\n=== {tagged.source} ==="
    print(header)
    if not tagged.entries:
        print("  (no entries)")
        return
    for te in tagged.entries:
        tag_str = ", ".join(te.tags) if te.tags else "untagged"
        label = _colorize(f"[{tag_str}]", "yellow") if color else f"[{tag_str}]"
        print(f"  {te.entry.key} {label}")


def cmd_tag(args: argparse.Namespace) -> int:
    directory = args.directory
    color = not getattr(args, "no_color", False)
    filter_tag: str | None = getattr(args, "tag", None)

    if not Path(directory).is_dir():
        msg = _colorize(f"Directory not found: {directory}", "red") if color else f"Directory not found: {directory}"
        print(msg, file=sys.stderr)
        return 2

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.")
        return 0

    exit_code = 0
    for path in env_files:
        try:
            parsed = _parse_env_file(path)
        except Exception as exc:  # noqa: BLE001
            print(f"  [error reading {path}: {exc}]", file=sys.stderr)
            continue

        tagged = tag_env_file(parsed)

        if filter_tag:
            matched = tagged.by_tag(filter_tag)
            if not matched:
                continue
            header = _colorize(f"\n=== {tagged.source} ===", "cyan") if color else f"\n=== {tagged.source} ==="
            print(header)
            for te in matched:
                label = _colorize(f"[{filter_tag}]", "yellow") if color else f"[{filter_tag}]"
                print(f"  {te.entry.key} {label}")
        else:
            _print_tagged(tagged, color=color)

    return exit_code


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("tag", help="Show semantic tags for .env keys")
    p.add_argument("directory", nargs="?", default=".", help="Directory to scan")
    p.add_argument("--tag", metavar="TAG", help="Filter output to a specific tag")
    p.add_argument("--no-color", action="store_true", help="Disable coloured output")
    p.set_defaults(_dispatch=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_tag(args)
