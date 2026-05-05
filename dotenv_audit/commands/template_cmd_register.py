"""Registration helpers and dispatch for the template subcommand."""
from __future__ import annotations

import argparse
from pathlib import Path

from dotenv_audit.commands.template_cmd import cmd_template


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach the *template* subcommand to *subparsers*."""
    p = subparsers.add_parser(
        "template",
        help="Generate a .env.template file from existing .env files.",
    )
    p.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    p.add_argument(
        "--output",
        default=".env.template",
        help="Output path for the generated template (default: .env.template).",
    )
    p.add_argument(
        "--no-comments",
        action="store_true",
        default=False,
        help="Omit inline comments from the generated template.",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    p.set_defaults(_dispatch=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    directory = Path(args.directory)
    output = Path(args.output)
    include_comments = not args.no_comments
    color = not args.no_color
    return cmd_template(
        directory=directory,
        output=output,
        include_comments=include_comments,
        color=color,
    )
