"""Tests for dotenv_audit.baseline."""

import json
import pytest

from dotenv_audit.baseline import (
    save_baseline,
    load_baseline,
    diff_against_baseline,
    DEFAULT_BASELINE_FILE,
)


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    baseline_file = str(tmp_path / "baseline.json")
    key_map = {".env": ["DB_URL", "SECRET_KEY"], ".env.prod": ["API_KEY"]}
    save_baseline(key_map, path=baseline_file)
    loaded = load_baseline(path=baseline_file)
    assert loaded[".env"] == ["DB_URL", "SECRET_KEY"]
    assert loaded[".env.prod"] == ["API_KEY"]


def test_save_sorts_keys(tmp_path):
    baseline_file = str(tmp_path / "baseline.json")
    save_baseline({".env": ["Z_KEY", "A_KEY", "M_KEY"]}, path=baseline_file)
    with open(baseline_file) as fh:
        data = json.load(fh)
    assert data[".env"] == ["A_KEY", "M_KEY", "Z_KEY"]


def test_load_returns_empty_when_missing(tmp_path):
    result = load_baseline(path=str(tmp_path / "nonexistent.json"))
    assert result == {}


# ---------------------------------------------------------------------------
# diff_against_baseline
# ---------------------------------------------------------------------------

def test_diff_no_changes():
    current = {".env": ["A", "B"]}
    baseline = {".env": ["A", "B"]}
    assert diff_against_baseline(current, baseline) == {}


def test_diff_detects_added_key():
    current = {".env": ["A", "B", "C"]}
    baseline = {".env": ["A", "B"]}
    result = diff_against_baseline(current, baseline)
    assert result[".env"]["added"] == ["C"]
    assert result[".env"]["removed"] == []


def test_diff_detects_removed_key():
    current = {".env": ["A"]}
    baseline = {".env": ["A", "B"]}
    result = diff_against_baseline(current, baseline)
    assert result[".env"]["removed"] == ["B"]
    assert result[".env"]["added"] == []


def test_diff_detects_new_file():
    current = {".env.staging": ["X", "Y"]}
    baseline = {}
    result = diff_against_baseline(current, baseline)
    assert result[".env.staging"]["new_file"] == ["X", "Y"]


def test_diff_ignores_files_only_in_baseline():
    """Files removed from disk are NOT reported – caller decides."""
    current = {}
    baseline = {".env": ["A"]}
    assert diff_against_baseline(current, baseline) == {}
