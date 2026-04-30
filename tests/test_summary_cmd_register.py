"""Tests for summary_cmd.register / _dispatch wiring."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

from dotenv_audit.commands.summary_cmd import _dispatch, register


def _make_subparsers() -> argparse._SubParsersAction:  # type: ignore[type-arg]
    parser = argparse.ArgumentParser()
    return parser.add_subparsers()


def test_register_adds_summary_subcommand() -> None:
    sp = _make_subparsers()
    register(sp)
    choices = sp.choices  # type: ignore[attr-defined]
    assert "summary" in choices


def test_register_no_color_flag() -> None:
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers()
    register(sp)
    parsed = parser.parse_args(["summary", "--no-color"])
    assert parsed.no_color is True


def test_dispatch_calls_cmd_summary(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=str(tmp_path), no_color=True)
    with patch("dotenv_audit.commands.summary_cmd.cmd_summary", return_value=0) as mock:
        result = _dispatch(args)
    mock.assert_called_once_with(args)
    assert result == 0


def test_dispatch_returns_exit_code_on_issues(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=str(tmp_path), no_color=True)
    with patch("dotenv_audit.commands.summary_cmd.cmd_summary", return_value=1):
        result = _dispatch(args)
    assert result == 1


def test_dispatch_returns_2_for_bad_directory() -> None:
    args = argparse.Namespace(directory="/no/such/path", no_color=True)
    result = _dispatch(args)
    assert result == 2
