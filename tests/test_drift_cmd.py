"""Tests for dotenv_audit.commands.drift_cmd."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from dotenv_audit.commands.drift_cmd import cmd_drift_check, register


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_env(tmp_path: Path, name: str, content: str) -> None:
    (tmp_path / name).write_text(content)


def _write_baseline(tmp_path: Path, data: dict) -> str:
    bp = tmp_path / ".env-baseline.json"
    bp.write_text(json.dumps(data))
    return str(bp)


def _make_args(directory: str, baseline: str) -> argparse.Namespace:
    return argparse.Namespace(directory=directory, baseline=baseline)


# ---------------------------------------------------------------------------
# cmd_drift_check
# ---------------------------------------------------------------------------

def test_drift_cmd_returns_0_when_no_drift(tmp_path, capsys):
    _write_env(tmp_path, ".env", "FOO=bar\n")
    bl = _write_baseline(tmp_path, {".env": {"FOO": "bar"}})
    args = _make_args(str(tmp_path), bl)
    assert cmd_drift_check(args) == 0
    out = capsys.readouterr().out
    assert "No drift" in out


def test_drift_cmd_returns_1_when_drift(tmp_path, capsys):
    _write_env(tmp_path, ".env", "FOO=bar\nNEW=extra\n")
    bl = _write_baseline(tmp_path, {".env": {"FOO": "bar"}})
    args = _make_args(str(tmp_path), bl)
    assert cmd_drift_check(args) == 1


def test_drift_cmd_prints_added_key(tmp_path, capsys):
    _write_env(tmp_path, ".env", "FOO=bar\nNEW=extra\n")
    bl = _write_baseline(tmp_path, {".env": {"FOO": "bar"}})
    args = _make_args(str(tmp_path), bl)
    cmd_drift_check(args)
    out = capsys.readouterr().out
    assert "NEW" in out


def test_drift_cmd_prints_removed_key(tmp_path, capsys):
    _write_env(tmp_path, ".env", "FOO=bar\n")
    bl = _write_baseline(tmp_path, {".env": {"FOO": "bar", "OLD": "gone"}})
    args = _make_args(str(tmp_path), bl)
    cmd_drift_check(args)
    out = capsys.readouterr().out
    assert "OLD" in out


def test_drift_cmd_prints_changed_key(tmp_path, capsys):
    _write_env(tmp_path, ".env", "FOO=new_val\n")
    bl = _write_baseline(tmp_path, {".env": {"FOO": "old_val"}})
    args = _make_args(str(tmp_path), bl)
    cmd_drift_check(args)
    out = capsys.readouterr().out
    assert "FOO" in out


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

def test_register_adds_drift_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    register(sub)
    parsed = root.parse_args(["drift", ".", "--baseline", "some.json"])
    assert parsed.directory == "."
    assert parsed.baseline == "some.json"
