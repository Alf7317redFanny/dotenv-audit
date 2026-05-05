"""Tests for dotenv_audit.pinner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.pinner import (
    PinEntry,
    PinSnapshot,
    diff_pin,
    load_pin,
    save_pin,
    snapshot_from_parsed,
)


def _entry(key: str, value: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, line_number=1)


def _parsed(path: str, entries) -> ParsedEnvFile:
    p = ParsedEnvFile(path=Path(path), entries=entries)
    return p


# --- snapshot_from_parsed ---

def test_snapshot_has_correct_source():
    parsed = _parsed(".env", [_entry("FOO", "bar")])
    snap = snapshot_from_parsed(parsed)
    assert snap.source == ".env"


def test_snapshot_marks_non_empty_value_as_has_value():
    parsed = _parsed(".env", [_entry("FOO", "bar")])
    snap = snapshot_from_parsed(parsed)
    assert snap.entries[0].has_value is True


def test_snapshot_marks_empty_value_as_no_value():
    parsed = _parsed(".env", [_entry("FOO", "")])
    snap = snapshot_from_parsed(parsed)
    assert snap.entries[0].has_value is False


def test_snapshot_skips_entries_without_key():
    parsed = _parsed(".env", [_entry("", "something"), _entry("BAR", "1")])
    snap = snapshot_from_parsed(parsed)
    assert len(snap.entries) == 1
    assert snap.entries[0].key == "BAR"


def test_snapshot_key_set():
    parsed = _parsed(".env", [_entry("A", "1"), _entry("B", "2")])
    snap = snapshot_from_parsed(parsed)
    assert snap.key_set() == {"A", "B"}


# --- save_pin / load_pin ---

def test_save_and_load_roundtrip(tmp_path):
    snap = PinSnapshot(
        source=".env",
        entries=[PinEntry(key="FOO", has_value=True), PinEntry(key="BAR", has_value=False)],
    )
    pin_file = tmp_path / "pin.json"
    save_pin(snap, pin_file)
    loaded = load_pin(pin_file)
    assert loaded.source == ".env"
    assert {e.key for e in loaded.entries} == {"FOO", "BAR"}


def test_load_returns_empty_snapshot_when_missing(tmp_path):
    snap = load_pin(tmp_path / "nonexistent.json")
    assert snap.source == ""
    assert snap.entries == []


def test_save_writes_valid_json(tmp_path):
    snap = PinSnapshot(source=".env.test", entries=[PinEntry(key="X", has_value=True)])
    pin_file = tmp_path / "pin.json"
    save_pin(snap, pin_file)
    data = json.loads(pin_file.read_text())
    assert data["source"] == ".env.test"
    assert data["entries"][0]["key"] == "X"


# --- diff_pin ---

def _snap(source, items):
    entries = [PinEntry(key=k, has_value=v) for k, v in items.items()]
    return PinSnapshot(source=source, entries=entries)


def test_diff_no_changes():
    old = _snap(".env", {"A": True, "B": False})
    new = _snap(".env", {"A": True, "B": False})
    diff = diff_pin(old, new)
    assert not diff.has_changes


def test_diff_detects_added_key():
    old = _snap(".env", {"A": True})
    new = _snap(".env", {"A": True, "B": True})
    diff = diff_pin(old, new)
    assert diff.added == ["B"]
    assert diff.has_changes


def test_diff_detects_removed_key():
    old = _snap(".env", {"A": True, "B": True})
    new = _snap(".env", {"A": True})
    diff = diff_pin(old, new)
    assert diff.removed == ["B"]


def test_diff_detects_filled_key():
    old = _snap(".env", {"SECRET": False})
    new = _snap(".env", {"SECRET": True})
    diff = diff_pin(old, new)
    assert diff.filled == ["SECRET"]
    assert diff.emptied == []


def test_diff_detects_emptied_key():
    old = _snap(".env", {"TOKEN": True})
    new = _snap(".env", {"TOKEN": False})
    diff = diff_pin(old, new)
    assert diff.emptied == ["TOKEN"]
    assert diff.filled == []


def test_diff_summary_no_changes():
    old = _snap(".env", {"A": True})
    diff = diff_pin(old, old)
    assert "no changes" in diff.summary()


def test_diff_summary_with_changes():
    old = _snap(".env", {"A": True})
    new = _snap(".env", {"A": True, "B": False})
    diff = diff_pin(old, new)
    assert "+1 added" in diff.summary()
