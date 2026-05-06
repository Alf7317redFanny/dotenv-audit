"""Tests for dotenv_audit.filterer."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.filterer import (
    FilterResult,
    filter_env_file,
    filter_many,
    _matches_pattern,
)


def _entry(key: str, value: str = "", flagged_reason: str | None = None) -> EnvEntry:
    return EnvEntry(key=key, value=value, flagged_reason=flagged_reason, line_number=1)


def _parsed(*entries: EnvEntry, path: str = ".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=list(entries))


# --- _matches_pattern ---

def test_matches_pattern_glob_exact():
    assert _matches_pattern("DB_HOST", "DB_HOST") is True


def test_matches_pattern_glob_wildcard():
    assert _matches_pattern("DB_HOST", "DB_*") is True


def test_matches_pattern_glob_no_match():
    assert _matches_pattern("API_KEY", "DB_*") is False


def test_matches_pattern_regex_match():
    assert _matches_pattern("SECRET_TOKEN", "re:^SECRET_") is True


def test_matches_pattern_regex_no_match():
    assert _matches_pattern("DB_PASS", "re:^SECRET_") is False


# --- filter_env_file ---

def test_filter_no_criteria_returns_all():
    parsed = _parsed(_entry("A"), _entry("B"), _entry("C"))
    result = filter_env_file(parsed)
    assert result.match_count == 3
    assert result.total == 3


def test_filter_by_glob_pattern():
    parsed = _parsed(_entry("DB_HOST"), _entry("DB_PASS"), _entry("API_KEY"))
    result = filter_env_file(parsed, pattern="DB_*")
    assert result.match_count == 2
    assert {e.key for e in result.matched} == {"DB_HOST", "DB_PASS"}


def test_filter_by_regex_pattern():
    parsed = _parsed(_entry("SECRET_KEY"), _entry("SECRET_TOKEN"), _entry("DB_HOST"))
    result = filter_env_file(parsed, pattern="re:SECRET")
    assert result.match_count == 2


def test_filter_secrets_only():
    parsed = _parsed(
        _entry("PLAIN", "hello"),
        _entry("TOKEN", "abc123", flagged_reason="hex token"),
    )
    result = filter_env_file(parsed, secrets_only=True)
    assert result.match_count == 1
    assert result.matched[0].key == "TOKEN"


def test_filter_empty_only():
    parsed = _parsed(
        _entry("FILLED", "value"),
        _entry("EMPTY", ""),
        _entry("BLANK", "   "),
    )
    result = filter_env_file(parsed, empty_only=True)
    assert result.match_count == 2


def test_filter_combined_pattern_and_secrets():
    parsed = _parsed(
        _entry("DB_PASS", "secret", flagged_reason="looks secret"),
        _entry("DB_HOST", "localhost"),
        _entry("API_SECRET", "xyz", flagged_reason="looks secret"),
    )
    result = filter_env_file(parsed, pattern="DB_*", secrets_only=True)
    assert result.match_count == 1
    assert result.matched[0].key == "DB_PASS"


def test_filter_result_summary():
    parsed = _parsed(_entry("A"), _entry("B"), path=".env.test")
    result = filter_env_file(parsed, pattern="A")
    assert "1/2" in result.summary()
    assert ".env.test" in result.summary()


# --- filter_many ---

def test_filter_many_returns_one_result_per_file():
    files = [
        _parsed(_entry("DB_HOST"), path=".env"),
        _parsed(_entry("API_KEY"), path=".env.prod"),
    ]
    results = filter_many(files, pattern="DB_*")
    assert len(results) == 2
    assert results[0].match_count == 1
    assert results[1].match_count == 0
