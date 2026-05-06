"""CLI commands for archiving and inspecting .env snapshots."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv_audit.archiver import (
    Archive,
    load_archive,
    save_archive,
    snapshot_directory,
)

_DEFAULT_ARCHIVE = ".env-audit-archive.json"


def cmd_archive_save(args: argparse.Namespace) -> int:
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    archive_path = Path(args.archive)
    archive = load_archive(archive_path)
    new_entries = snapshot_directory(directory)

    if not new_entries:
        print("No .env files found — nothing archived.")
        return 0

    for entry in new_entries:
        archive.add(entry)

    save_archive(archive, archive_path)
    print(f"Archived {len(new_entries)} file(s) to {archive_path}")
    return 0


def cmd_archive_history(args: argparse.Namespace) -> int:
    archive_path = Path(args.archive)
    archive = load_archive(archive_path)

    path_filter: str = args.env_path
    history = archive.history_for(path_filter)

    if not history:
        print(f"No history found for: {path_filter}")
        return 1

    print(f"History for {path_filter} ({len(history)} snapshot(s)):")
    for entry in history:
        import datetime
        ts = datetime.datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  [{ts}]  keys={len(entry.keys)}  secrets={entry.secret_count}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("archive", help="snapshot and inspect .env history")
    sub = parser.add_subparsers(dest="archive_cmd")

    p_save = sub.add_parser("save", help="snapshot current .env files into the archive")
    p_save.add_argument("directory", nargs="?", default=".", help="project directory")
    p_save.add_argument("--archive", default=_DEFAULT_ARCHIVE, help="archive file path")

    p_hist = sub.add_parser("history", help="show snapshot history for a file")
    p_hist.add_argument("env_path", help="relative path of the .env file")
    p_hist.add_argument("--archive", default=_DEFAULT_ARCHIVE, help="archive file path")

    parser.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    if args.archive_cmd == "save":
        return cmd_archive_save(args)
    if args.archive_cmd == "history":
        return cmd_archive_history(args)
    print("Usage: dotenv-audit archive {save|history}", file=sys.stderr)
    return 2
