"""CLI sub-command: ``dotenv-audit watch``."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from dotenv_audit.parser import parse_env_file
from dotenv_audit.reporter import report_secrets
from dotenv_audit.watcher import watch


def _on_change(paths: list[Path], *, color: bool) -> None:
    """Callback invoked by the watcher whenever files change."""
    print(f"\n[watch] {len(paths)} file(s) changed — re-running audit...")
    for p in sorted(paths):
        if not p.exists():
            print(f"  [deleted] {p}")
            continue
        parsed = parse_env_file(p)
        output = report_secrets(parsed, color=color)
        print(output)


def cmd_watch(args: argparse.Namespace) -> int:
    """Entry point for the *watch* sub-command.

    Returns 0 always (the watcher runs until interrupted).
    """
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: '{directory}' is not a directory or does not exist.")
        return 2

    color: bool = not args.no_color
    interval: float = float(args.interval)

    print(f"[watch] Watching '{directory}' every {interval}s — press Ctrl+C to stop.")
    try:
        watch(
            directory,
            lambda paths: _on_change(paths, color=color),
            poll_interval=interval,
        )
    except KeyboardInterrupt:
        print("\n[watch] Stopped.")

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "watch",
        help="Watch a directory for .env file changes and re-audit on the fly.",
    )
    p.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to watch (default: current directory).",
    )
    p.add_argument(
        "--interval",
        default=2.0,
        type=float,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 2.0).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable coloured output.",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_watch(args)
