"""CLI sub-command: drift  — detect changes vs a saved baseline."""

from __future__ import annotations

import argparse
import sys

from dotenv_audit.drift import detect_drift
from dotenv_audit.reporter import _colorize


def cmd_drift_check(args: argparse.Namespace) -> int:
    """Run drift detection and print a human-readable report."""
    reports = detect_drift(args.directory, args.baseline)

    drifted = [r for r in reports if r.has_drift]

    if not drifted:
        print(_colorize("green", "✔  No drift detected across all env files."))
        return 0

    print(_colorize("red", f"✘  Drift detected in {len(drifted)} file(s):\n"))
    for report in drifted:
        print(f"  {_colorize('yellow', report.env_path)}  —  {report.summary()}")
        for key in report.added:
            print(f"    {_colorize('green', f'+ {key}')}  (new key)")
        for key in report.removed:
            print(f"    {_colorize('red', f'- {key}')}  (removed key)")
        for key in report.changed:
            print(f"    {_colorize('yellow', f'~ {key}')}  (value changed)")
        print()

    return 1


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "drift",
        help="Detect drift between current env files and a saved baseline.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--baseline",
        default=".env-baseline.json",
        help="Path to baseline JSON file (default: .env-baseline.json).",
    )
    parser.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> None:
    sys.exit(cmd_drift_check(args))
