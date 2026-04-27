"""Command-line interface for dotenv-audit."""

import argparse
import sys
from pathlib import Path

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.comparator import compare_many
from dotenv_audit.reporter import full_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dotenv-audit",
        description="Scan project directories for .env files and audit secrets/key mismatches.",
    )
    p.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    p.add_argument(
        "--reference",
        metavar="FILE",
        help="Reference .env file to compare all others against (e.g. .env.example)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output",
    )
    p.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with code 1 if any secrets or mismatches are found",
    )
    return p


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.directory).resolve()
    if not root.is_dir():
        print(f"Error: '{root}' is not a directory.", file=sys.stderr)
        return 2

    env_paths = scan_directory(root)
    if not env_paths:
        print("No .env files found.")
        return 0

    parsed_files = [ParsedEnvFile.from_file(p) for p in env_paths]

    comparisons = []
    if args.reference:
        ref_path = Path(args.reference).resolve()
        ref_parsed = ParsedEnvFile.from_file(str(ref_path))
        others = [pf for pf in parsed_files if pf.path != str(ref_path)]
        comparisons = compare_many(ref_parsed, others)

    use_color = not args.no_color
    report = full_report(parsed_files, comparisons, use_color=use_color)
    print(report)

    if args.fail_on_issues:
        has_secrets = any(pf.flagged_entries() for pf in parsed_files)
        has_mismatches = any(c.has_issues for c in comparisons)
        if has_secrets or has_mismatches:
            return 1

    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
