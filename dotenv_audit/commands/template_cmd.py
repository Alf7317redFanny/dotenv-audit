"""CLI command: generate .env.example templates from discovered env files."""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.scanner import scan_directory
from dotenv_audit.templater import EnvTemplate, build_templates


def _write_template(template: EnvTemplate, output_dir: str) -> str:
    """Write a template file next to its source and return the output path."""
    source_dir = os.path.dirname(os.path.abspath(template.source_path))
    base_name = os.path.basename(template.source_path)
    out_name = base_name + ".example"
    out_path = os.path.join(output_dir or source_dir, out_name)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(template.render())
        fh.write("\n")
    return out_path


def cmd_template(
    directory: str,
    output_dir: str | None = None,
    annotate: bool = True,
    dry_run: bool = False,
    no_color: bool = False,
) -> int:
    if not os.path.isdir(directory):
        print(f"error: directory not found: {directory}", file=sys.stderr)
        return 2

    env_paths = scan_directory(directory)
    if not env_paths:
        print("No .env files found.")
        return 0

    parsed_files: List[ParsedEnvFile] = []
    for path in env_paths:
        try:
            parsed_files.append(ParsedEnvFile.from_file(path))
        except Exception as exc:  # noqa: BLE001
            print(f"warning: could not parse {path}: {exc}", file=sys.stderr)

    templates = build_templates(parsed_files, annotate_secrets=annotate)

    for tmpl in templates:
        if dry_run:
            print(f"[dry-run] would write template for {tmpl.source_path} ({tmpl.key_count} keys)")
        else:
            dest = _write_template(tmpl, output_dir or "")
            print(f"wrote {dest} ({tmpl.key_count} keys)")

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p: argparse.ArgumentParser = subparsers.add_parser(
        "template",
        help="Generate .env.example template files from discovered .env files.",
    )
    p.add_argument("directory", nargs="?", default=".", help="Root directory to scan.")
    p.add_argument("--output-dir", default=None, help="Directory to write templates into.")
    p.add_argument("--no-annotate", action="store_true", help="Omit secret annotation comments.")
    p.add_argument("--dry-run", action="store_true", help="Print actions without writing files.")
    p.add_argument("--no-color", action="store_true", help="Disable colored output.")
    p.set_defaults(_dispatch=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    return cmd_template(
        directory=args.directory,
        output_dir=args.output_dir,
        annotate=not args.no_annotate,
        dry_run=args.dry_run,
        no_color=args.no_color,
    )
