"""Tests for dotenv_audit.commands.lint_cmd."""
from __future__ import annotations

import argparse
import os

import pytest

from dotenv_audit.commands.lint_cmd import cmd_lint


def _make_args(directory: str) -> argparse.Namespace:
    return argparse.Namespace(directory=directory)


def _write_env(tmp_path, filename: str, content: str) -> str:
    p = tmp_path / filename
    p.write_text(content)
    return str(p)


def test_lint_cmd_returns_2_for_missing_directory(tmp_path):
    args = _make_args(str(tmp_path / "nonexistent"))
    assert cmd_lint(args) == 2


def test_lint_cmd_returns_0_when_no_files(tmp_path):
    args = _make_args(str(tmp_path))
    assert cmd_lint(args) == 0


def test_lint_cmd_returns_0_for_clean_file(tmp_path, capsys):
    _write_env(tmp_path, ".env", "DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\n")
    args = _make_args(str(tmp_path))
    result = cmd_lint(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "passed" in out


def test_lint_cmd_returns_1_for_lowercase_key(tmp_path, capsys):
    _write_env(tmp_path, ".env", "database_url=postgres://localhost/db\n")
    args = _make_args(str(tmp_path))
    result = cmd_lint(args)
    assert result == 1
    out = capsys.readouterr().out
    assert "issue" in out


def test_lint_cmd_returns_1_for_empty_value(tmp_path, capsys):
    _write_env(tmp_path, ".env", "SECRET_KEY=\n")
    args = _make_args(str(tmp_path))
    result = cmd_lint(args)
    assert result == 1
    out = capsys.readouterr().out
    assert "empty" in out


def test_lint_cmd_multiple_files(tmp_path, capsys):
    _write_env(tmp_path, ".env", "API_KEY=abc\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / ".env.staging").write_text("bad_key=value\n")
    args = _make_args(str(tmp_path))
    result = cmd_lint(args)
    # one clean, one with lowercase key
    assert result == 1
    out = capsys.readouterr().out
    assert "2 file" in out or "issue" in out
