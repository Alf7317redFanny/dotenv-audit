"""CLI sub-command: lint — check .env files for style issues."""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import parse_env_file
from dotenv_audit.linter import LintResult, lint_env_file


def cmd_lint(args: argparse.Namespace) -> int:
    directory = args.directory

    if not os.path.isdir(directory):
        print(f"error: '{directory}' is not a directory", file=sys.stderr)
        return 2

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.")
        return 0

    results: List[LintResult] = []
    for path in env_files:
        parsed = parse_env_file(path)
        results.append(lint_env_file(parsed))

    any_issues = False
    for result in results:
        print(result.summary)
        if result.has_issues:
            any_issues = True

    if any_issues:
        total = sum(len(r.issues) for r in results)
        print(f"\n{total} lint issue(s) found across {len(results)} file(s).")
        return 1

    print(f"\nAll {len(results)} file(s) passed lint checks.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("lint", help="lint .env files for style issues")
    p.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="directory to scan (default: current directory)",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_lint(args)
