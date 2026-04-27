"""Tests for dotenv_audit.comparator module."""

import pytest

from dotenv_audit.comparator import (
    ComparisonResult,
    compare_env_files,
    compare_many,
)
from dotenv_audit.parser import ParsedEnvFile, EnvEntry


def _make_parsed(path: str, keys: list[str]) -> ParsedEnvFile:
    entries = [EnvEntry(key=k, value="value", line_number=i + 1, raw_line=f"{k}=value") for i, k in enumerate(keys)]
    return ParsedEnvFile(path=path, entries=entries)


def test_compare_identical_files_no_issues():
    ref = _make_parsed(".env", ["DB_URL", "SECRET_KEY", "DEBUG"])
    cmp = _make_parsed(".env.production", ["DB_URL", "SECRET_KEY", "DEBUG"])
    result = compare_env_files(ref, cmp)
    assert not result.has_issues
    assert result.missing_in_compared == []
    assert result.extra_in_compared == []


def test_compare_detects_missing_keys():
    ref = _make_parsed(".env", ["DB_URL", "SECRET_KEY", "DEBUG"])
    cmp = _make_parsed(".env.production", ["DB_URL"])
    result = compare_env_files(ref, cmp)
    assert result.has_issues
    assert "SECRET_KEY" in result.missing_in_compared
    assert "DEBUG" in result.missing_in_compared


def test_compare_detects_extra_keys():
    ref = _make_parsed(".env", ["DB_URL"])
    cmp = _make_parsed(".env.staging", ["DB_URL", "NEW_FEATURE_FLAG"])
    result = compare_env_files(ref, cmp)
    assert result.has_issues
    assert "NEW_FEATURE_FLAG" in result.extra_in_compared
    assert result.missing_in_compared == []


def test_compare_common_keys_populated():
    ref = _make_parsed(".env", ["A", "B", "C"])
    cmp = _make_parsed(".env.test", ["B", "C", "D"])
    result = compare_env_files(ref, cmp)
    assert set(result.common_keys) == {"B", "C"}


def test_summary_no_issues():
    ref = _make_parsed(".env", ["KEY"])
    cmp = _make_parsed(".env.prod", ["KEY"])
    result = compare_env_files(ref, cmp)
    assert "No key mismatches" in result.summary()


def test_summary_shows_missing_and_extra():
    ref = _make_parsed(".env", ["A", "B"])
    cmp = _make_parsed(".env.prod", ["B", "C"])
    result = compare_env_files(ref, cmp)
    summary = result.summary()
    assert "Missing" in summary
    assert "A" in summary
    assert "Extra" in summary
    assert "C" in summary


def test_compare_many_returns_one_result_per_file():
    ref = _make_parsed(".env", ["A", "B"])
    others = [
        _make_parsed(".env.staging", ["A"]),
        _make_parsed(".env.prod", ["A", "B"]),
        _make_parsed(".env.test", ["A", "B", "C"]),
    ]
    results = compare_many(ref, others)
    assert len(results) == 3
    assert results[0].has_issues
    assert not results[1].has_issues
    assert results[2].has_issues


def test_compare_empty_reference():
    ref = _make_parsed(".env", [])
    cmp = _make_parsed(".env.prod", ["SECRET"])
    result = compare_env_files(ref, cmp)
    assert "SECRET" in result.extra_in_compared
    assert result.missing_in_compared == []
