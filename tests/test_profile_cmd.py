"""Tests for dotenv_audit.commands.profile_cmd."""
from __future__ import annotations

import argparse
import os

import pytest

from dotenv_audit.commands.profile_cmd import cmd_profile, register, _dispatch


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_args(directory: str = ".", no_color: bool = False) -> argparse.Namespace:
    return argparse.Namespace(directory=directory, no_color=no_color)


def _write_env(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# cmd_profile
# ---------------------------------------------------------------------------

def test_profile_cmd_returns_2_for_missing_directory(tmp_path):
    result = cmd_profile(str(tmp_path / "nonexistent"))
    assert result == 2


def test_profile_cmd_returns_0_when_no_files(tmp_path):
    result = cmd_profile(str(tmp_path))
    assert result == 0


def test_profile_cmd_returns_0_for_clean_file(tmp_path):
    _write_env(str(tmp_path / ".env"), "NAME=alice\nENV=production\n")
    result = cmd_profile(str(tmp_path), color=False)
    assert result == 0


def test_profile_cmd_returns_1_for_file_with_secret(tmp_path):
    secret = "a" * 40
    _write_env(str(tmp_path / ".env"), f"TOKEN={secret}\n")
    result = cmd_profile(str(tmp_path), color=False)
    assert result == 1


def test_profile_cmd_returns_1_for_lint_issues(tmp_path):
    # duplicate key triggers a lint issue
    _write_env(str(tmp_path / ".env"), "KEY=one\nKEY=two\n")
    result = cmd_profile(str(tmp_path), color=False)
    assert result == 1


def test_profile_cmd_no_color_does_not_raise(tmp_path):
    _write_env(str(tmp_path / ".env"), "A=\nB=\n")
    result = cmd_profile(str(tmp_path), color=False)
    assert result in (0, 1)


# ---------------------------------------------------------------------------
# register / _dispatch
# ---------------------------------------------------------------------------

def _make_subparsers():
    root = argparse.ArgumentParser()
    return root, root.add_subparsers()


def test_register_adds_profile_subcommand():
    _, subs = _make_subparsers()
    register(subs)
    # no error means it registered correctly


def test_register_defaults_directory_to_dot():
    root, subs = _make_subparsers()
    register(subs)
    args = root.parse_args(["profile"])
    assert args.directory == "."


def test_register_no_color_flag():
    root, subs = _make_subparsers()
    register(subs)
    args = root.parse_args(["profile", "--no-color"])
    assert args.no_color is True


def test_dispatch_calls_cmd_profile(tmp_path):
    args = _make_args(directory=str(tmp_path))
    args._dispatch = _dispatch
    result = _dispatch(args)
    assert result == 0
