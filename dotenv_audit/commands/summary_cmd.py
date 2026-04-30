"""CLI command: summarize audit results for a directory."""
from __future__ import annotations

import argparse

from dotenv_audit.summarizer import build_summary


def cmd_summary(args: argparse.Namespace) -> int:
    """Print a high-level audit summary and return an exit code."""
    import os

    directory = args.directory
    if not os.path.isdir(directory):
        print(f"[error] directory not found: {directory}")
        return 2

    summary = build_summary(directory)

    use_color = not getattr(args, "no_color", False)

    def _c(text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if use_color else text

    print(_c(f"Directory : {directory}", "1"))
    print(f"  Files scanned  : {summary.total_files}")
    print(f"  Secrets found  : {summary.total_secrets}")
    print(f"  Lint issues    : {summary.total_lint_issues}")

    if summary.comparison is not None:
        cmp = summary.comparison
        print(f"  Missing keys   : {len(cmp.missing_keys)}")
        print(f"  Extra keys     : {len(cmp.extra_keys)}")

    if summary.has_issues:
        print(_c("\nStatus: ISSUES FOUND", "31"))
        return 1

    print(_c("\nStatus: OK", "32"))
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "summary",
        help="Print a high-level audit summary for a directory.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to audit (default: current directory).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable coloured output.",
    )
    parser.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_summary(args)
