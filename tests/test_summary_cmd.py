"""Tests for the summary CLI command."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

from dotenv_audit.commands.summary_cmd import cmd_summary, register


def _make_args(directory: str, no_color: bool = True) -> argparse.Namespace:
    return argparse.Namespace(directory=directory, no_color=no_color)


def _write_env(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_summary_cmd_returns_2_for_missing_directory(tmp_path: Path) -> None:
    args = _make_args(str(tmp_path / "nonexistent"))
    assert cmd_summary(args) == 2


def test_summary_cmd_returns_0_when_no_files(tmp_path: Path) -> None:
    args = _make_args(str(tmp_path))
    assert cmd_summary(args) == 0


def test_summary_cmd_returns_0_for_clean_file(tmp_path: Path) -> None:
    _write_env(tmp_path / ".env", "APP_NAME=myapp\nDEBUG=false\n")
    args = _make_args(str(tmp_path))
    assert cmd_summary(args) == 0


def test_summary_cmd_returns_1_when_secrets_found(tmp_path: Path) -> None:
    _write_env(
        tmp_path / ".env",
        "SECRET_KEY=a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2\n",
    )
    args = _make_args(str(tmp_path))
    assert cmd_summary(args) == 1


def test_summary_cmd_prints_file_count(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:  # type: ignore[type-arg]
    _write_env(tmp_path / ".env", "APP_NAME=myapp\n")
    _write_env(tmp_path / ".env.local", "APP_NAME=myapp\n")
    args = _make_args(str(tmp_path))
    cmd_summary(args)
    out = capsys.readouterr().out
    assert "Files scanned  : 2" in out


def test_register_adds_summary_subcommand() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    parsed = parser.parse_args(["summary", "."])
    assert parsed.directory == "."


def test_register_defaults_directory_to_dot() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    parsed = parser.parse_args(["summary"])
    assert parsed.directory == "."


def test_register_sets_dispatch_func() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    parsed = parser.parse_args(["summary"])
    assert callable(parsed.func)
