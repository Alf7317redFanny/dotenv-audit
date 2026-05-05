"""CLI sub-command: profile — show per-file health metrics."""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import parse_env_file
from dotenv_audit.profiler import profile_many, EnvProfile
from dotenv_audit.reporter import _colorize


def _fmt_ratio(ratio: float, color: bool) -> str:
    pct = f"{ratio * 100:.0f}%"
    if ratio >= 0.5:
        return _colorize(pct, "red") if color else pct
    if ratio > 0.0:
        return _colorize(pct, "yellow") if color else pct
    return pct


def cmd_profile(directory: str, color: bool = True) -> int:
    """Print health profiles for all .env files found under *directory*.

    Returns 0 when no issues are found, 1 when at least one file has
    lint issues or secrets, 2 when the directory does not exist.
    """
    if not os.path.isdir(directory):
        print(f"[error] directory not found: {directory}", file=sys.stderr)
        return 2

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.")
        return 0

    parsed = [parse_env_file(f) for f in env_files]
    profiles: List[EnvProfile] = profile_many(parsed)

    has_issues = False
    for prof in profiles:
        header = f"── {prof.path} "
        print(header + "─" * max(0, 60 - len(header)))
        print(f"  Keys    : {prof.total_keys}")
        print(f"  Empty   : {prof.empty_keys}  ({_fmt_ratio(prof.empty_ratio, color)})")
        print(f"  Secrets : {prof.secret_keys}  ({_fmt_ratio(prof.secret_ratio, color)})")
        print(f"  Score   : {prof.score}")
        if prof.lint_result.has_issues():
            print(f"  Lint    : {prof.lint_result.summary()}")
            has_issues = True
        else:
            print("  Lint    : ok")
        if prof.secret_keys > 0:
            has_issues = True
        print()

    return 1 if has_issues else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "profile",
        help="Show per-file health metrics (keys, empties, secrets, score, lint).",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    parser.set_defaults(_dispatch=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_profile(
        directory=args.directory,
        color=not args.no_color,
    )
