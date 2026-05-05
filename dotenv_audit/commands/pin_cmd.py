"""CLI sub-commands for pinning .env key state and checking drift against a pin."""
from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path

from dotenv_audit.parser import parse_env_file
from dotenv_audit.pinner import diff_pin, load_pin, save_pin, snapshot_from_parsed
from dotenv_audit.scanner import scan_directory

_DEFAULT_PIN = ".env-pin.json"


def cmd_pin_save(args: Namespace) -> int:
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found — nothing to pin.")
        return 0

    pin_path = Path(args.pin_file)
    # Build a combined snapshot keyed by relative path
    combined: dict = {}
    for f in env_files:
        parsed = parse_env_file(f)
        snap = snapshot_from_parsed(parsed)
        rel = str(Path(f).relative_to(directory))
        snap.source = rel
        combined[rel] = snap

    # Persist each snapshot individually using source as stem
    pin_path.write_text(
        __import__("json").dumps(
            {
                rel: {
                    "source": s.source,
                    "entries": [{"key": e.key, "has_value": e.has_value} for e in s.entries],
                }
                for rel, s in combined.items()
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(f"Pinned {len(combined)} file(s) to {pin_path}")
    return 0


def cmd_pin_check(args: Namespace) -> int:
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    pin_path = Path(args.pin_file)
    if not pin_path.exists():
        print(f"error: pin file not found: {pin_path}", file=sys.stderr)
        return 2

    raw = __import__("json").loads(pin_path.read_text())
    env_files = scan_directory(directory)
    exit_code = 0

    for f in env_files:
        parsed = parse_env_file(f)
        rel = str(Path(f).relative_to(directory))
        new_snap = snapshot_from_parsed(parsed)
        new_snap.source = rel

        if rel in raw:
            from dotenv_audit.pinner import PinEntry, PinSnapshot
            old_entries = [PinEntry(key=e["key"], has_value=e["has_value"]) for e in raw[rel]["entries"]]
            old_snap = PinSnapshot(source=rel, entries=old_entries)
        else:
            from dotenv_audit.pinner import PinSnapshot
            old_snap = PinSnapshot(source=rel)

        diff = diff_pin(old_snap, new_snap)
        color = "" if args.no_color else ("\033[33m" if diff.has_changes else "\033[32m")
        reset = "" if args.no_color else "\033[0m"
        print(f"{color}{diff.summary()}{reset}")
        if diff.has_changes:
            exit_code = 1

    return exit_code


def register(subparsers: _SubParsersAction) -> None:
    p: ArgumentParser = subparsers.add_parser("pin", help="pin .env key state")
    p.add_argument("action", choices=["save", "check"])
    p.add_argument("--directory", default=".")
    p.add_argument("--pin-file", default=_DEFAULT_PIN)
    p.add_argument("--no-color", action="store_true")
    p.set_defaults(func=_dispatch)


def _dispatch(args: Namespace) -> int:
    if args.action == "save":
        return cmd_pin_save(args)
    return cmd_pin_check(args)
