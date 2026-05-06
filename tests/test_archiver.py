"""Tests for dotenv_audit.archiver."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from dotenv_audit.archiver import (
    Archive,
    ArchiveEntry,
    load_archive,
    save_archive,
    snapshot_directory,
)


def _entry(path: str = ".env", keys=None, secret_count: int = 0, ts: float = 0.0) -> ArchiveEntry:
    return ArchiveEntry(path=path, keys=keys or ["KEY"], secret_count=secret_count, timestamp=ts)


# ── ArchiveEntry ─────────────────────────────────────────────────────────────

def test_entry_roundtrip():
    e = _entry(keys=["A", "B"], secret_count=2, ts=1_700_000_000.0)
    assert ArchiveEntry.from_dict(e.to_dict()) == e


def test_entry_to_dict_contains_expected_keys():
    d = _entry().to_dict()
    assert set(d) == {"path", "keys", "secret_count", "timestamp"}


# ── Archive ───────────────────────────────────────────────────────────────────

def test_archive_latest_for_returns_none_when_empty():
    assert Archive().latest_for(".env") is None


def test_archive_latest_for_returns_most_recent():
    a = Archive()
    a.add(_entry(ts=1.0))
    a.add(_entry(ts=3.0))
    a.add(_entry(ts=2.0))
    assert a.latest_for(".env").timestamp == 3.0


def test_archive_history_for_is_sorted_ascending():
    a = Archive()
    a.add(_entry(ts=5.0))
    a.add(_entry(ts=1.0))
    a.add(_entry(ts=3.0))
    history = a.history_for(".env")
    assert [e.timestamp for e in history] == [1.0, 3.0, 5.0]


def test_archive_history_for_filters_by_path():
    a = Archive()
    a.add(_entry(path=".env", ts=1.0))
    a.add(_entry(path=".env.local", ts=2.0))
    assert len(a.history_for(".env")) == 1


# ── Persistence ───────────────────────────────────────────────────────────────

def test_save_and_load_roundtrip(tmp_path):
    archive = Archive()
    archive.add(_entry(keys=["X", "Y"], secret_count=1, ts=1_000.0))
    dest = tmp_path / "archive.json"
    save_archive(archive, dest)
    loaded = load_archive(dest)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].keys == ["X", "Y"]


def test_load_returns_empty_when_missing(tmp_path):
    a = load_archive(tmp_path / "nonexistent.json")
    assert a.entries == []


def test_save_produces_valid_json(tmp_path):
    archive = Archive()
    archive.add(_entry())
    dest = tmp_path / "archive.json"
    save_archive(archive, dest)
    data = json.loads(dest.read_text())
    assert isinstance(data, list)
    assert data[0]["path"] == ".env"


# ── snapshot_directory ────────────────────────────────────────────────────────

def test_snapshot_empty_directory(tmp_path):
    result = snapshot_directory(tmp_path)
    assert result == []


def test_snapshot_creates_entry_per_env_file(tmp_path):
    (tmp_path / ".env").write_text("KEY=value\n")
    (tmp_path / ".env.local").write_text("OTHER=value\n")
    entries = snapshot_directory(tmp_path)
    assert len(entries) == 2
    paths = {e.path for e in entries}
    assert ".env" in paths
    assert ".env.local" in paths


def test_snapshot_entry_has_correct_key_list(tmp_path):
    (tmp_path / ".env").write_text("FOO=bar\nBAZ=qux\n")
    entries = snapshot_directory(tmp_path)
    assert set(entries[0].keys) == {"FOO", "BAZ"}


def test_snapshot_entry_counts_secrets(tmp_path):
    token = "a" * 32  # looks like a hex token
    (tmp_path / ".env").write_text(f"TOKEN={token}\n")
    entries = snapshot_directory(tmp_path)
    assert entries[0].secret_count >= 1
