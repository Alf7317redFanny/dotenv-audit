"""CLI command: dotenv-audit rotate — check key rotation staleness."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from dotenv_audit.parser import parse_env_file
from dotenv_audit.rotator import check_rotation
from dotenv_audit.scanner import scan_directory


def _load_rotation_map(map_path: Path) -> Dict[str, datetime]:
    """Load a JSON file mapping key names to ISO-8601 timestamps."""
    if not map_path.exists():
        return {}
    with map_path.open() as fh:
        raw: Dict[str, str] = json.load(fh)
    result: Dict[str, datetime] = {}
    for key, ts in raw.items():
        try:
            result[key] = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass
    return result


def cmd_rotate(
    directory: str,
    rotation_map_path: str,
    max_age_days: int,
    no_color: bool,
) -> int:
    root = Path(directory)
    if not root.is_dir():
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    rotation_map = _load_rotation_map(Path(rotation_map_path))
    env_files = scan_directory(root)

    if not env_files:
        print("No .env files found.")
        return 0

    any_stale = False
    for env_path in env_files:
        try:
            parsed = parse_env_file(str(env_path))
        except Exception as exc:  # pragma: no cover
            print(f"warning: could not parse {env_path}: {exc}", file=sys.stderr)
            continue

        report = check_rotation(parsed, rotation_map, max_age_days=max_age_days)
        print(report.summary())
        for entry in report.entries:
            if entry.is_stale:
                marker = "[STALE]" if no_color else "\033[31m[STALE]\033[0m"
                print(f"  {marker} {entry}")

        if report.has_stale:
            any_stale = True

    return 1 if any_stale else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "rotate",
        help="check key rotation staleness across .env files",
    )
    p.add_argument("directory", nargs="?", default=".", help="project root to scan")
    p.add_argument(
        "--rotation-map",
        default=".rotation_map.json",
        dest="rotation_map",
        help="JSON file mapping keys to last-rotated ISO timestamps",
    )
    p.add_argument(
        "--max-age-days",
        type=int,
        default=90,
        dest="max_age_days",
        help="number of days before a key is considered stale (default: 90)",
    )
    p.add_argument("--no-color", action="store_true", default=False)
    p.set_defaults(dispatch=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_rotate(
        directory=args.directory,
        rotation_map_path=args.rotation_map,
        max_age_days=args.max_age_days,
        no_color=args.no_color,
    )
