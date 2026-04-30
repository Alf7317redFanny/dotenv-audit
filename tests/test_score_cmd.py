"""Tests for dotenv_audit.commands.score_cmd."""
from __future__ import annotations

import argparse
import os

import pytest

from dotenv_audit.commands.score_cmd import cmd_score


def _make_args(directory: str, no_color: bool = True) -> argparse.Namespace:
    return argparse.Namespace(directory=directory, no_color=no_color)


def _write_env(tmp_path, name: str, content: str) -> None:
    (tmp_path / name).write_text(content)


def test_score_cmd_returns_2_for_missing_directory(tmp_path):
    args = _make_args(str(tmp_path / "nonexistent"))
    assert cmd_score(args) == 2


def test_score_cmd_returns_0_when_no_files(tmp_path):
    args = _make_args(str(tmp_path))
    assert cmd_score(args) == 0


def test_score_cmd_returns_0_for_clean_file(tmp_path, capsys):
    _write_env(tmp_path, ".env", "APP_NAME=myapp\nDEBUG=false\n")
    args = _make_args(str(tmp_path))
    rc = cmd_score(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert ".env" in out


def test_score_cmd_returns_1_for_high_risk_file(tmp_path):
    token = "a" * 40
    _write_env(tmp_path, ".env", f"SECRET_KEY={token}\n")
    args = _make_args(str(tmp_path))
    rc = cmd_score(args)
    assert rc == 1


def test_score_cmd_output_contains_score_label(tmp_path, capsys):
    _write_env(tmp_path, ".env", "FOO=bar\n")
    args = _make_args(str(tmp_path))
    cmd_score(args)
    out = capsys.readouterr().out
    assert "score=" in out
    assert "secrets=" in out


def test_score_cmd_multiple_files_sorted_highest_first(tmp_path, capsys):
    token = "b" * 40
    _write_env(tmp_path, ".env", f"TOKEN={token}\n")
    _write_env(tmp_path, ".env.example", "TOKEN=changeme\n")
    args = _make_args(str(tmp_path))
    cmd_score(args)
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    # risky file should appear before the clean example
    assert ".env" in lines[0]
