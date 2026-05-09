"""Tests for dotenv_audit.censor."""

from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.censor import (
    CensoredEntry,
    CensoredEnvFile,
    _censor_value,
    censor_env_file,
    censor_many,
)


def _entry(key: str, value: str, flag: str | None = None) -> EnvEntry:
    return EnvEntry(key=key, value=value, flag=flag, line_number=1)


def _parsed(*entries: EnvEntry, path: str = ".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=list(entries))


# --- _censor_value ---

def test_censor_value_empty_returns_empty():
    assert _censor_value("") == ""


def test_censor_value_full_mask():
    assert _censor_value("supersecret") == "***"


def test_censor_value_partial_short_value_still_fully_masked():
    # value too short for partial reveal
    assert _censor_value("abc", partial=True) == "***"


def test_censor_value_partial_long_value_shows_prefix():
    result = _censor_value("abcdefghij", partial=True)
    assert result.startswith("abcd")
    assert "***" in result
    assert "efghij" not in result


# --- censor_env_file ---

def test_censor_env_file_plain_value_not_censored():
    parsed = _parsed(_entry("HOST", "localhost"))
    result = censor_env_file(parsed)
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert not entry.was_censored
    assert entry.censored_value == "localhost"


def test_censor_env_file_flagged_value_is_censored():
    parsed = _parsed(_entry("SECRET", "abc123def456", flag="hex_token"))
    result = censor_env_file(parsed)
    entry = result.entries[0]
    assert entry.was_censored
    assert entry.censored_value == "***"
    assert entry.original_value == "abc123def456"


def test_censor_env_file_empty_flagged_value_not_censored():
    # flag present but value is empty — nothing to censor
    parsed = _parsed(_entry("SECRET", "", flag="hex_token"))
    result = censor_env_file(parsed)
    entry = result.entries[0]
    assert not entry.was_censored


def test_censor_env_file_censored_keys_list():
    parsed = _parsed(
        _entry("HOST", "localhost"),
        _entry("TOKEN", "ghp_abc123xyz", flag="github_pat"),
    )
    result = censor_env_file(parsed)
    assert result.censored_keys == ["TOKEN"]


def test_censor_env_file_lines_output():
    parsed = _parsed(_entry("KEY", "value"), _entry("SEC", "s3cr3t", flag="hex_token"))
    result = censor_env_file(parsed)
    assert result.lines == ["KEY=value", "SEC=***"]


def test_censor_env_file_summary_no_censored():
    parsed = _parsed(_entry("A", "1"))
    result = censor_env_file(parsed)
    assert "no values censored" in result.summary()


def test_censor_env_file_summary_with_censored():
    parsed = _parsed(_entry("T", "tok", flag="hex_token"))
    result = censor_env_file(parsed)
    assert "1 value(s) censored" in result.summary()


def test_censor_env_file_partial_mode():
    parsed = _parsed(_entry("KEY", "abcdefghij", flag="hex_token"))
    result = censor_env_file(parsed, partial=True)
    entry = result.entries[0]
    assert entry.censored_value.startswith("abcd")
    assert entry.was_censored


# --- censor_many ---

def test_censor_many_returns_one_per_file():
    files = [
        _parsed(_entry("A", "1"), path=".env"),
        _parsed(_entry("B", "tok", flag="hex_token"), path=".env.prod"),
    ]
    results = censor_many(files)
    assert len(results) == 2
    assert results[1].censored_keys == ["B"]


def test_censor_many_empty_list():
    assert censor_many([]) == []
