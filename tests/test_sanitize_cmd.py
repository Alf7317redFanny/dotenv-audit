"""Tests for dotenv_audit.commands.sanitize_cmd."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from dotenv_audit.commands.sanitize_cmd import cmd_sanitize, register, _dispatch


def _make_args(directory: str, write: bool = False, no_color: bool = True) -> argparse.Namespace:
    return argparse.Namespace(directory=directory, write=write, no_color=no_color)


def _write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_sanitize_cmd_returns_2_for_missing_directory(tmp_path):
    args = _make_args(str(tmp_path / "nonexistent"))
    assert cmd_sanitize(args) == 2


def test_sanitize_cmd_returns_0_when_no_files(tmp_path):
    args = _make_args(str(tmp_path))
    assert cmd_sanitize(args) == 0


def test_sanitize_cmd_returns_0_for_clean_file(tmp_path):
    _write_env(tmp_path, ".env", "KEY=value\nOTHER=123\n")
    args = _make_args(str(tmp_path))
    assert cmd_sanitize(args) == 0


def test_sanitize_cmd_returns_1_for_dirty_file(tmp_path):
    _write_env(tmp_path, ".env", "KEY=hello\x00world\n")
    args = _make_args(str(tmp_path))
    assert cmd_sanitize(args) == 1


def test_sanitize_cmd_write_rewrites_file(tmp_path):
    env = _write_env(tmp_path, ".env", "KEY=hello\x00world\n")
    args = _make_args(str(tmp_path), write=True)
    code = cmd_sanitize(args)
    assert code == 1
    content = env.read_text()
    assert "\x00" not in content
    assert "KEY=helloworld" in content


def test_sanitize_cmd_write_does_not_touch_clean_file(tmp_path):
    env = _write_env(tmp_path, ".env", "KEY=clean\n")
    original_mtime = env.stat().st_mtime
    args = _make_args(str(tmp_path), write=True)
    cmd_sanitize(args)
    # file should not be rewritten if clean
    assert env.stat().st_mtime == original_mtime


def test_dispatch_calls_cmd_sanitize(tmp_path):
    args = _make_args(str(tmp_path))
    assert _dispatch(args) == 0


def test_register_adds_sanitize_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    parsed = parser.parse_args(["sanitize", "."])
    assert parsed.directory == "."


def test_register_defaults_directory_to_dot():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    parsed = parser.parse_args(["sanitize"])
    assert parsed.directory == "."


def test_register_write_flag():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    parsed = parser.parse_args(["sanitize", "--write"])
    assert parsed.write is True
