"""CLI command: validate .env files against a JSON schema."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List

from dotenv_audit.parser import parse_env_file
from dotenv_audit.scanner import scan_directory
from dotenv_audit.validator import validate_env_file, ValidationResult


def _load_schema(schema_path: str) -> dict:
    """Load a JSON schema file mapping key names to type strings."""
    with open(schema_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def cmd_validate(args: argparse.Namespace) -> int:
    """Run schema validation against all discovered .env files."""
    directory = args.directory
    if not os.path.isdir(directory):
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    schema_path = args.schema
    if not os.path.isfile(schema_path):
        print(f"error: schema file not found: {schema_path}", file=sys.stderr)
        return 2

    try:
        schema = _load_schema(schema_path)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"error: could not load schema: {exc}", file=sys.stderr)
        return 2

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.")
        return 0

    results: List[ValidationResult] = []
    for path in env_files:
        parsed = parse_env_file(path)
        result = validate_env_file(
            parsed, schema, require_all=not args.no_require_all
        )
        results.append(result)

    any_issues = False
    for result in results:
        if result.has_issues or args.verbose:
            print(result.summary)
        if result.has_issues:
            any_issues = True

    if not any_issues:
        print(f"All {len(results)} file(s) passed schema validation.")
        return 0

    return 1


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "validate",
        help="validate .env files against a JSON schema",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--schema",
        default=".env.schema.json",
        help="path to JSON schema file (default: .env.schema.json)",
    )
    parser.add_argument(
        "--no-require-all",
        action="store_true",
        default=False,
        help="do not flag keys present in schema but missing from file",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="print results for all files, not just those with issues",
    )
    parser.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_validate(args)
