"""Tests for dotenv_audit.sorter."""
import pytest
from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.sorter import (
    SortResult,
    sort_env_file,
    sort_many,
    rewrite_sorted,
)


def _entry(key: str, value: str = "val", comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment)


def _parsed(path: str, entries) -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=list(entries))


def test_sort_result_already_sorted_str():
    r = SortResult(path=".env", original_order=["A", "B"], sorted_order=["A", "B"], changed=False)
    assert "already sorted" in str(r)


def test_sort_result_changed_str():
    r = SortResult(path=".env", original_order=["B", "A"], sorted_order=["A", "B"], changed=True)
    assert ".env" in str(r)


def test_sort_env_file_already_sorted():
    parsed = _parsed(".env", [_entry("ALPHA"), _entry("BETA"), _entry("GAMMA")])
    result = sort_env_file(parsed)
    assert not result.changed
    assert result.sorted_order == ["ALPHA", "BETA", "GAMMA"]


def test_sort_env_file_needs_sorting():
    parsed = _parsed(".env", [_entry("ZEBRA"), _entry("APPLE"), _entry("MANGO")])
    result = sort_env_file(parsed)
    assert result.changed
    assert result.sorted_order == ["APPLE", "MANGO", "ZEBRA"]


def test_sort_env_file_case_insensitive():
    parsed = _parsed(".env", [_entry("beta"), _entry("ALPHA")])
    result = sort_env_file(parsed)
    assert result.sorted_order == ["ALPHA", "beta"]


def test_sort_env_file_reverse():
    parsed = _parsed(".env", [_entry("ALPHA"), _entry("BETA"), _entry("GAMMA")])
    result = sort_env_file(parsed, reverse=True)
    assert result.sorted_order == ["GAMMA", "BETA", "ALPHA"]
    assert result.changed


def test_sort_env_file_empty():
    parsed = _parsed(".env", [])
    result = sort_env_file(parsed)
    assert not result.changed
    assert result.sorted_order == []


def test_sort_env_file_single_entry():
    parsed = _parsed(".env", [_entry("ONLY")])
    result = sort_env_file(parsed)
    assert not result.changed


def test_rewrite_sorted_returns_lines():
    parsed = _parsed(".env", [_entry("ZEBRA", "1"), _entry("APPLE", "2")])
    result = sort_env_file(parsed)
    lines = rewrite_sorted(parsed, result)
    assert lines[0] == "APPLE=2"
    assert lines[1] == "ZEBRA=1"


def test_rewrite_sorted_includes_comment():
    parsed = _parsed(".env", [_entry("B", "1", comment="# second"), _entry("A", "2")])
    result = sort_env_file(parsed)
    lines = rewrite_sorted(parsed, result)
    assert "A=2" in lines
    assert any("second" in ln for ln in lines)


def test_sort_many_returns_one_result_per_file():
    files = [
        _parsed(".env", [_entry("B"), _entry("A")]),
        _parsed(".env.local", [_entry("X"), _entry("Y")]),
    ]
    results = sort_many(files)
    assert len(results) == 2
    assert results[0].changed
    assert not results[1].changed


def test_sort_many_empty_list():
    assert sort_many([]) == []
