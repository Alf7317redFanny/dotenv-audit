"""CLI sub-command: baseline  (save / check)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.baseline import (
    save_baseline,
    load_baseline,
    diff_against_baseline,
    DEFAULT_BASELINE_FILE,
)


def _build_key_map(root: str) -> Dict[str, List[str]]:
    """Scan *root* and return {relative_path: [keys]} for every env file."""
    key_map: Dict[str, List[str]] = {}
    for env_path in scan_directory(root):
        parsed = ParsedEnvFile(env_path)
        rel = str(Path(env_path).relative_to(root))
        key_map[rel] = parsed.keys()
    return key_map


def cmd_baseline_save(args: argparse.Namespace) -> int:
    key_map = _build_key_map(args.directory)
    save_baseline(key_map, path=args.baseline)
    print(f"Baseline saved to {args.baseline} ({len(key_map)} file(s) tracked).")
    return 0


def cmd_baseline_check(args: argparse.Namespace) -> int:
    baseline = load_baseline(path=args.baseline)
    if not baseline:
        print(f"No baseline found at {args.baseline}. Run 'baseline save' first.", file=sys.stderr)
        return 2

    current = _build_key_map(args.directory)
    diffs = diff_against_baseline(current, baseline)

    if not diffs:
        print("Baseline check passed — no key changes detected.")
        return 0

    print("Baseline check FAILED — key changes detected:\n")
    for file_path, changes in sorted(diffs.items()):
        print(f"  {file_path}")
        if changes.get("new_file"):
            print(f"    [new file] keys: {', '.join(changes['new_file'])}")
        if changes.get("added"):
            print(f"    [added]   {', '.join(changes['added'])}")
        if changes.get("removed"):
            print(f"    [removed] {', '.join(changes['removed'])}")
    return 1


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach baseline sub-commands to an existing subparsers group."""
    parser = subparsers.add_parser("baseline", help="Save or check an env-key baseline.")
    parser.add_argument(
        "action", choices=["save", "check"], help="'save' writes baseline; 'check' diffs against it."
    )
    parser.add_argument(
        "directory", nargs="?", default=".", help="Project root to scan (default: current directory)."
    )
    parser.add_argument(
        "--baseline", default=DEFAULT_BASELINE_FILE, help="Path to baseline JSON file."
    )
    parser.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    if args.action == "save":
        return cmd_baseline_save(args)
    return cmd_baseline_check(args)
