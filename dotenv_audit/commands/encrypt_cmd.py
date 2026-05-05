"""CLI command: encrypt secrets in .env files using a Fernet key."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.encryptor import generate_key, encrypt_env_file


def _parse_env_file(path: str) -> ParsedEnvFile:
    from dotenv_audit.parser import parse_env_file  # local import to avoid circulars
    return parse_env_file(path)


def cmd_encrypt(args: argparse.Namespace) -> int:
    directory = args.directory
    if not os.path.isdir(directory):
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    key = args.key or os.environ.get("DOTENV_AUDIT_KEY")
    if not key:
        key = generate_key()
        print(f"Generated new key (store this securely): {key}")

    env_files = scan_directory(directory)
    if not env_files:
        print("No .env files found.")
        return 0

    total_encrypted = 0
    for path in env_files:
        try:
            parsed = _parse_env_file(path)
        except Exception as exc:
            print(f"warning: could not parse {path}: {exc}", file=sys.stderr)
            continue

        result = encrypt_env_file(parsed, key)
        if not result.encrypted_keys:
            continue

        if args.dry_run:
            print(f"[dry-run] {path}: would encrypt {result.encrypted_keys}")
        else:
            new_content = "\n".join(result.lines) + "\n"
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_content)
            label = "no-color" if args.no_color else "\033[33m"
            reset = "" if args.no_color else "\033[0m"
            print(f"{label}{path}{reset}: encrypted {result.encrypted_keys}")

        total_encrypted += len(result.encrypted_keys)

    if total_encrypted == 0:
        print("No secrets needed encryption.")
    else:
        print(f"\nTotal secrets encrypted: {total_encrypted}")

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "encrypt",
        help="Encrypt flagged secret values in .env files",
    )
    p.add_argument("directory", nargs="?", default=".", help="Directory to scan")
    p.add_argument("--key", default=None, help="Fernet key (or set DOTENV_AUDIT_KEY env var)")
    p.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    p.add_argument("--no-color", action="store_true", help="Disable colored output")
    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_encrypt(args)
