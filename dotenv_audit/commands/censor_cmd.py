"""CLI command: censor — print .env files with secret values masked."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.censor import censor_env_file, CensoredEnvFile


def _parse_env_file(path: str) -> ParsedEnvFile:
    from dotenv_audit.parser import parse_env_file  # local import to keep startup fast
    return parse_env_file(path)


def _print_censored(censored: CensoredEnvFile, no_color: bool) -> None:
    header = f"=== {censored.source} ==="
    if not no_color and censored.censored_keys:
        header = f"\033[33m{header}\033[0m"
    print(header)
    for line in censored.lines:
        print(line)
    print(censored.summary())
    print()


def cmd_censor(
    directory: str,
    partial: bool = False,
    no_color: bool = False,
    out=None,
) -> int:
    if out is None:
        out = sys.stdout

    if not os.path.isdir(directory):
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.", file=out)
        return 0

    any_censored = False
    for path in env_files:
        parsed = _parse_env_file(path)
        censored = censor_env_file(parsed, partial=partial)
        _print_censored(censored, no_color=no_color)
        if censored.censored_keys:
            any_censored = True

    return 1 if any_censored else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "censor",
        help="Print .env files with secret values masked.",
    )
    p.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory).",
    )
    p.add_argument(
        "--partial",
        action="store_true",
        default=False,
        help="Show first few characters of secrets instead of fully masking.",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output.",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_censor(
        directory=args.directory,
        partial=args.partial,
        no_color=args.no_color,
    )
