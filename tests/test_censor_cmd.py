"""Tests for dotenv_audit.commands.censor_cmd."""

from __future__ import annotations

import argparse
import os

import pytest

from dotenv_audit.commands.censor_cmd import cmd_censor, register, _dispatch


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"directory": ".", "partial": False, "no_color": True, "func": _dispatch}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _write_env(tmp_path, filename: str, content: str) -> str:
    p = tmp_path / filename
    p.write_text(content)
    return str(p)


def test_censor_cmd_returns_2_for_missing_directory(tmp_path):
    result = cmd_censor(str(tmp_path / "nonexistent"))
    assert result == 2


def test_censor_cmd_returns_0_when_no_files(tmp_path):
    result = cmd_censor(str(tmp_path))
    assert result == 0


def test_censor_cmd_returns_0_for_clean_file(tmp_path):
    _write_env(tmp_path, ".env", "HOST=localhost\nPORT=5432\n")
    result = cmd_censor(str(tmp_path), no_color=True)
    assert result == 0


def test_censor_cmd_returns_1_when_secrets_found(tmp_path):
    _write_env(
        tmp_path,
        ".env",
        "HOST=localhost\nSECRET_KEY=a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4\n",
    )
    result = cmd_censor(str(tmp_path), no_color=True)
    assert result == 1


def test_censor_cmd_partial_flag_accepted(tmp_path):
    _write_env(
        tmp_path,
        ".env",
        "TOKEN=abcdefghijklmnop\n",
    )
    # should not raise; partial mode just changes display
    result = cmd_censor(str(tmp_path), partial=True, no_color=True)
    assert result in (0, 1)


def test_register_adds_censor_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    args = parser.parse_args(["censor"])
    assert args.directory == "."
    assert args.partial is False
    assert args.no_color is False


def test_register_sets_dispatch_func():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    args = parser.parse_args(["censor"])
    assert callable(args.func)


def test_dispatch_calls_cmd_censor(tmp_path, monkeypatch):
    called_with = {}

    def fake_cmd(directory, partial=False, no_color=False):
        called_with["directory"] = directory
        called_with["partial"] = partial
        called_with["no_color"] = no_color
        return 0

    monkeypatch.setattr(
        "dotenv_audit.commands.censor_cmd.cmd_censor", fake_cmd
    )
    args = _make_args(directory=str(tmp_path), partial=True, no_color=True)
    result = _dispatch(args)
    assert result == 0
    assert called_with["partial"] is True
    assert called_with["no_color"] is True
