"""Tests for dotenv_audit.commands.rename_cmd."""

import argparse
from pathlib import Path

import pytest

from dotenv_audit.commands.rename_cmd import cmd_rename, register, _dispatch


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        directory=".",
        old_key="OLD",
        new_key="NEW",
        dry_run=False,
        no_color=True,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _write_env(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# error paths
# ---------------------------------------------------------------------------

def test_rename_cmd_returns_2_for_missing_directory(tmp_path):
    args = _make_args(directory=str(tmp_path / "nonexistent"))
    assert cmd_rename(args) == 2


def test_rename_cmd_returns_2_when_keys_identical(tmp_path):
    args = _make_args(directory=str(tmp_path), old_key="SAME", new_key="SAME")
    assert cmd_rename(args) == 2


# ---------------------------------------------------------------------------
# happy paths
# ---------------------------------------------------------------------------

def test_rename_cmd_returns_0_when_no_files(tmp_path):
    args = _make_args(directory=str(tmp_path))
    assert cmd_rename(args) == 0


def test_rename_cmd_returns_0_and_renames(tmp_path, capsys):
    _write_env(tmp_path / ".env", "OLD=secret\nDEBUG=true\n")
    args = _make_args(directory=str(tmp_path), old_key="OLD", new_key="NEW")
    code = cmd_rename(args)
    assert code == 0
    assert "NEW=secret" in (tmp_path / ".env").read_text()
    captured = capsys.readouterr()
    assert "NEW" in captured.out


def test_rename_cmd_dry_run_does_not_write(tmp_path, capsys):
    original = "OLD=secret\n"
    _write_env(tmp_path / ".env", original)
    args = _make_args(directory=str(tmp_path), old_key="OLD", new_key="NEW", dry_run=True)
    code = cmd_rename(args)
    assert code == 0
    assert (tmp_path / ".env").read_text() == original
    captured = capsys.readouterr()
    assert "dry-run" in captured.out


def test_rename_cmd_reports_not_found_key(tmp_path, capsys):
    _write_env(tmp_path / ".env", "UNRELATED=value\n")
    args = _make_args(directory=str(tmp_path), old_key="GHOST", new_key="NEW")
    code = cmd_rename(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "not found" in captured.out


# ---------------------------------------------------------------------------
# register / _dispatch
# ---------------------------------------------------------------------------

def _make_subparsers():
    root = argparse.ArgumentParser()
    return root.add_subparsers()


def test_register_adds_rename_subcommand():
    sp = _make_subparsers()
    register(sp)
    root = sp._name_parser_map
    assert "rename" in root


def test_register_defaults_directory_to_dot():
    sp = _make_subparsers()
    register(sp)
    parsed = sp._name_parser_map["rename"].parse_args(["A", "B"])
    assert parsed.directory == "."


def test_dispatch_calls_cmd_rename(tmp_path):
    args = _make_args(directory=str(tmp_path))
    assert _dispatch(args) == 0
