"""Tests for dotenv_audit.merger."""
from __future__ import annotations

import pytest

from dotenv_audit.merger import MergeConflict, MergeResult, merge_env_files
from dotenv_audit.parser import EnvEntry, ParsedEnvFile


def _entry(key: str, value: str, comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, raw=f"{key}={value}")


def _parsed(path: str, pairs: dict) -> ParsedEnvFile:
    entries = {k: _entry(k, v) for k, v in pairs.items()}
    return ParsedEnvFile(path=path, entries=entries)


# ---------------------------------------------------------------------------
# MergeConflict
# ---------------------------------------------------------------------------

def test_merge_conflict_str():
    c = MergeConflict(key="SECRET", sources=[".env.dev", ".env.prod"])
    assert "SECRET" in str(c)
    assert ".env.dev" in str(c)
    assert ".env.prod" in str(c)


# ---------------------------------------------------------------------------
# MergeResult
# ---------------------------------------------------------------------------

def test_merge_result_no_conflicts():
    result = MergeResult(entries={"A": _entry("A", "1")}, conflicts=[])
    assert not result.has_conflicts


def test_merge_result_has_conflicts():
    c = MergeConflict(key="X", sources=["a", "b"])
    result = MergeResult(entries={}, conflicts=[c])
    assert result.has_conflicts


def test_merge_result_summary_no_conflicts():
    result = MergeResult(entries={"A": _entry("A", "1"), "B": _entry("B", "2")}, conflicts=[])
    assert "2 key(s)" in result.summary
    assert "no conflicts" in result.summary


def test_merge_result_summary_with_conflicts():
    c = MergeConflict(key="FOO", sources=["x", "y"])
    result = MergeResult(entries={"FOO": _entry("FOO", "bar")}, conflicts=[c])
    assert "1 conflict" in result.summary
    assert "FOO" in result.summary


def test_merge_result_to_lines_sorted():
    result = MergeResult(
        entries={"Z": _entry("Z", "last"), "A": _entry("A", "first")},
        conflicts=[],
    )
    lines = result.to_lines()
    assert lines[0].startswith("A=")
    assert lines[1].startswith("Z=")


def test_merge_result_to_lines_with_comment():
    result = MergeResult(
        entries={"KEY": _entry("KEY", "val", comment="important")},
        conflicts=[],
    )
    lines = result.to_lines()
    assert "# important" in lines[0]


# ---------------------------------------------------------------------------
# merge_env_files
# ---------------------------------------------------------------------------

def test_merge_empty_list():
    result = merge_env_files([])
    assert result.entries == {}
    assert not result.has_conflicts


def test_merge_single_file():
    pf = _parsed(".env", {"A": "1", "B": "2"})
    result = merge_env_files([pf])
    assert set(result.entries.keys()) == {"A", "B"}
    assert not result.has_conflicts


def test_merge_two_disjoint_files():
    a = _parsed(".env.dev", {"DEV_KEY": "dev"})
    b = _parsed(".env.prod", {"PROD_KEY": "prod"})
    result = merge_env_files([a, b])
    assert "DEV_KEY" in result.entries
    assert "PROD_KEY" in result.entries
    assert not result.has_conflicts


def test_merge_later_file_wins():
    a = _parsed(".env", {"KEY": "old"})
    b = _parsed(".env.local", {"KEY": "new"})
    result = merge_env_files([a, b])
    assert result.entries["KEY"].value == "new"


def test_merge_detects_conflict():
    a = _parsed(".env.dev", {"DB_URL": "dev-db"})
    b = _parsed(".env.prod", {"DB_URL": "prod-db"})
    result = merge_env_files([a, b])
    assert result.has_conflicts
    assert result.conflicts[0].key == "DB_URL"
    assert ".env.dev" in result.conflicts[0].sources
    assert ".env.prod" in result.conflicts[0].sources


def test_merge_conflict_count():
    a = _parsed("a", {"X": "1", "Y": "2"})
    b = _parsed("b", {"X": "10", "Z": "3"})
    result = merge_env_files([a, b])
    assert len(result.conflicts) == 1
    assert result.conflicts[0].key == "X"
