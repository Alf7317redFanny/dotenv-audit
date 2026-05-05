"""Tests for dotenv_audit.differ."""
from __future__ import annotations

import pytest

from dotenv_audit.differ import DiffLine, DiffResult, diff_env_files
from dotenv_audit.parser import EnvEntry, ParsedEnvFile


def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", lineno=1, comment=None)


def _parsed(path: str, pairs: list[tuple[str, str]]) -> ParsedEnvFile:
    entries = [_entry(k, v) for k, v in pairs]
    return ParsedEnvFile(path=path, entries=entries)


def test_diff_identical_files_no_changes():
    left = _parsed(".env", [("A", "1"), ("B", "2")])
    right = _parsed(".env.prod", [("A", "1"), ("B", "2")])
    result = diff_env_files(left, right)
    assert not result.has_changes


def test_diff_detects_added_key():
    left = _parsed(".env", [("A", "1")])
    right = _parsed(".env.prod", [("A", "1"), ("B", "2")])
    result = diff_env_files(left, right)
    assert result.has_changes
    added = [ln for ln in result.lines if ln.kind == "added"]
    assert len(added) == 1
    assert added[0].key == "B"
    assert added[0].new_value == "2"


def test_diff_detects_removed_key():
    left = _parsed(".env", [("A", "1"), ("B", "2")])
    right = _parsed(".env.prod", [("A", "1")])
    result = diff_env_files(left, right)
    removed = [ln for ln in result.lines if ln.kind == "removed"]
    assert len(removed) == 1
    assert removed[0].key == "B"
    assert removed[0].old_value == "2"


def test_diff_detects_changed_value():
    left = _parsed(".env", [("SECRET", "old")])
    right = _parsed(".env.prod", [("SECRET", "new")])
    result = diff_env_files(left, right)
    changed = [ln for ln in result.lines if ln.kind == "changed"]
    assert len(changed) == 1
    assert changed[0].key == "SECRET"
    assert changed[0].old_value == "old"
    assert changed[0].new_value == "new"


def test_diff_summary_no_changes():
    left = _parsed(".env", [("X", "1")])
    right = _parsed(".env.prod", [("X", "1")])
    result = diff_env_files(left, right)
    assert result.summary == "No differences found."


def test_diff_summary_mixed_changes():
    left = _parsed(".env", [("A", "1"), ("B", "old")])
    right = _parsed(".env.prod", [("B", "new"), ("C", "3")])
    result = diff_env_files(left, right)
    assert result.has_changes
    summary = result.summary
    assert "added" in summary
    assert "removed" in summary
    assert "changed" in summary


def test_diff_line_str_added():
    line = DiffLine("added", "FOO", new_value="bar")
    assert str(line) == "+ FOO=bar"


def test_diff_line_str_removed():
    line = DiffLine("removed", "FOO", old_value="bar")
    assert str(line) == "- FOO=bar"


def test_diff_line_str_changed():
    line = DiffLine("changed", "FOO", old_value="a", new_value="b")
    assert "~" in str(line)
    assert "FOO" in str(line)


def test_diff_preserves_key_order():
    left = _parsed(".env", [("Z", "1"), ("A", "2")])
    right = _parsed(".env.prod", [("Z", "1"), ("A", "2")])
    result = diff_env_files(left, right)
    assert not result.has_changes


def test_diff_empty_files():
    """Two empty env files should produce no diff lines and no changes."""
    left = _parsed(".env", [])
    right = _parsed(".env.prod", [])
    result = diff_env_files(left, right)
    assert not result.has_changes
    assert result.lines == []
    assert result.summary == "No differences found."


def test_diff_one_empty_one_populated():
    """All keys from the populated file should appear as added."""
    left = _parsed(".env", [])
    right = _parsed(".env.prod", [("A", "1"), ("B", "2")])
    result = diff_env_files(left, right)
    assert result.has_changes
    added = [ln for ln in result.lines if ln.kind == "added"]
    assert len(added) == 2
    assert {ln.key for ln in added} == {"A", "B"}
