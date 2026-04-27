"""Integration-style tests for the baseline CLI sub-command."""

import argparse
import json
from pathlib import Path

import pytest

from dotenv_audit.commands.baseline_cmd import (
    cmd_baseline_save,
    cmd_baseline_check,
    _build_key_map,
)
from dotenv_audit.baseline import DEFAULT_BASELINE_FILE


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_env(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def _make_args(directory: str, baseline: str, action: str = "save") -> argparse.Namespace:
    return argparse.Namespace(directory=directory, baseline=baseline, action=action)


# ---------------------------------------------------------------------------
# _build_key_map
# ---------------------------------------------------------------------------

def test_build_key_map_returns_keys(tmp_path):
    _write_env(tmp_path, ".env", "DB_URL=postgres://localhost\nSECRET=abc123\n")
    result = _build_key_map(str(tmp_path))
    assert ".env" in result
    assert "DB_URL" in result[".env"]
    assert "SECRET" in result[".env"]


def test_build_key_map_empty_dir(tmp_path):
    result = _build_key_map(str(tmp_path))
    assert result == {}


# ---------------------------------------------------------------------------
# cmd_baseline_save
# ---------------------------------------------------------------------------

def test_save_creates_baseline_file(tmp_path):
    _write_env(tmp_path, ".env", "KEY=value\n")
    baseline_file = str(tmp_path / "baseline.json")
    args = _make_args(str(tmp_path), baseline_file)
    rc = cmd_baseline_save(args)
    assert rc == 0
    assert Path(baseline_file).exists()
    data = json.loads(Path(baseline_file).read_text())
    assert ".env" in data


# ---------------------------------------------------------------------------
# cmd_baseline_check
# ---------------------------------------------------------------------------

def test_check_passes_when_no_changes(tmp_path):
    _write_env(tmp_path, ".env", "KEY=value\n")
    baseline_file = str(tmp_path / "baseline.json")
    save_args = _make_args(str(tmp_path), baseline_file, action="save")
    cmd_baseline_save(save_args)

    check_args = _make_args(str(tmp_path), baseline_file, action="check")
    rc = cmd_baseline_check(check_args)
    assert rc == 0


def test_check_fails_when_key_added(tmp_path):
    _write_env(tmp_path, ".env", "KEY=value\n")
    baseline_file = str(tmp_path / "baseline.json")
    cmd_baseline_save(_make_args(str(tmp_path), baseline_file))

    # Add a new key after saving baseline
    _write_env(tmp_path, ".env", "KEY=value\nNEW_KEY=extra\n")
    rc = cmd_baseline_check(_make_args(str(tmp_path), baseline_file, action="check"))
    assert rc == 1


def test_check_returns_2_when_no_baseline(tmp_path):
    baseline_file = str(tmp_path / "nonexistent.json")
    rc = cmd_baseline_check(_make_args(str(tmp_path), baseline_file, action="check"))
    assert rc == 2
