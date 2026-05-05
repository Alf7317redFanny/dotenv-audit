"""Tests for template_cmd registration and dispatch."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from dotenv_audit.commands.template_cmd_register import register, _dispatch


def _make_subparsers() -> argparse._SubParsersAction:  # type: ignore[type-arg]
    parser = argparse.ArgumentParser()
    return parser.add_subparsers()


def test_register_adds_template_subcommand():
    sp = _make_subparsers()
    register(sp)
    choices = sp.choices  # type: ignore[attr-defined]
    assert "template" in choices


def test_register_defaults_directory_to_dot():
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers()
    register(sp)
    args = parser.parse_args(["template"])
    assert args.directory == "."


def test_register_defaults_output():
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers()
    register(sp)
    args = parser.parse_args(["template"])
    assert args.output == ".env.template"


def test_register_no_color_flag():
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers()
    register(sp)
    args = parser.parse_args(["template", "--no-color"])
    assert args.no_color is True


def test_register_no_comments_flag():
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers()
    register(sp)
    args = parser.parse_args(["template", "--no-comments"])
    assert args.no_comments is True


def test_dispatch_calls_cmd_template(tmp_path):
    args = argparse.Namespace(
        directory=str(tmp_path),
        output=str(tmp_path / ".env.template"),
        no_comments=False,
        no_color=False,
    )
    with patch(
        "dotenv_audit.commands.template_cmd_register.cmd_template", return_value=0
    ) as mock_cmd:
        result = _dispatch(args)
    mock_cmd.assert_called_once_with(
        directory=Path(str(tmp_path)),
        output=Path(str(tmp_path / ".env.template")),
        include_comments=True,
        color=True,
    )
    assert result == 0


def test_dispatch_returns_exit_code():
    args = argparse.Namespace(
        directory="/nonexistent",
        output="/nonexistent/.env.template",
        no_comments=True,
        no_color=True,
    )
    with patch(
        "dotenv_audit.commands.template_cmd_register.cmd_template", return_value=2
    ):
        result = _dispatch(args)
    assert result == 2
