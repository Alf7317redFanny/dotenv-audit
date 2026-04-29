"""Tests for dotenv_audit.commands.redact_cmd."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from dotenv_audit.commands.redact_cmd import cmd_redact


def _make_args(directory: str, in_place: bool = False, verbose: bool = False) -> argparse.Namespace:
    return argparse.Namespace(directory=directory, in_place=in_place, verbose=verbose)


def _write_env(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_redact_cmd_returns_0_when_no_files(tmp_path: Path) -> None:
    args = _make_args(str(tmp_path))
    assert cmd_redact(args) == 0


def test_redact_cmd_returns_2_for_missing_directory() -> None:
    args = _make_args("/nonexistent/path/xyz")
    assert cmd_redact(args) == 2


def test_redact_cmd_returns_0_when_no_secrets(tmp_path: Path) -> None:
    _write_env(tmp_path / ".env", "APP_NAME=myapp\nDEBUG=true\n")
    args = _make_args(str(tmp_path))
    assert cmd_redact(args) == 0


def test_redact_cmd_returns_1_when_secrets_found_no_in_place(tmp_path: Path, capsys) -> None:
    _write_env(tmp_path / ".env", "SECRET_KEY=abcdef1234567890abcdef1234567890\n")
    args = _make_args(str(tmp_path), in_place=False)
    result = cmd_redact(args)
    assert result == 1
    captured = capsys.readouterr()
    assert "REDACTED" in captured.out


def test_redact_cmd_in_place_overwrites_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    _write_env(env_file, "SECRET_KEY=abcdef1234567890abcdef1234567890\nAPP=ok\n")
    args = _make_args(str(tmp_path), in_place=True)
    result = cmd_redact(args)
    assert result == 0
    content = env_file.read_text(encoding="utf-8")
    assert "REDACTED" in content
    assert "abcdef1234567890abcdef1234567890" not in content


def test_redact_cmd_in_place_preserves_clean_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    _write_env(env_file, "SECRET_KEY=abcdef1234567890abcdef1234567890\nAPP_NAME=myapp\n")
    args = _make_args(str(tmp_path), in_place=True)
    cmd_redact(args)
    content = env_file.read_text(encoding="utf-8")
    assert "APP_NAME=myapp" in content


def test_redact_cmd_verbose_prints_clean_files(tmp_path: Path, capsys) -> None:
    _write_env(tmp_path / ".env", "APP_NAME=myapp\n")
    args = _make_args(str(tmp_path), verbose=True)
    cmd_redact(args)
    captured = capsys.readouterr()
    assert "[clean]" in captured.out
