"""Tests for dotenv_audit.scorer."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.scorer import FileScore, _level, score_file, score_many


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", lineno=1)


def _parsed(path: str, entries: list) -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=entries)


# ---------------------------------------------------------------------------
# _level
# ---------------------------------------------------------------------------

def test_level_zero_is_low():
    assert _level(0) == "low"


def test_level_small_is_medium():
    assert _level(5) == "medium"


def test_level_mid_is_high():
    assert _level(20) == "high"


def test_level_large_is_critical():
    assert _level(50) == "critical"


# ---------------------------------------------------------------------------
# score_file
# ---------------------------------------------------------------------------

def test_score_file_clean_returns_low():
    parsed = _parsed(".env", [_entry("APP_NAME", "myapp")])
    result = score_file(parsed)
    assert result.level == "low"
    assert result.score == 0
    assert result.secret_count == 0


def test_score_file_with_secret_raises_score():
    # a 40-char hex string looks like a secret
    token = "a" * 40
    parsed = _parsed(".env", [_entry("SECRET_KEY", token)])
    result = score_file(parsed)
    assert result.secret_count >= 1
    assert result.score >= 10


def test_score_file_empty_value_adds_to_score():
    parsed = _parsed(".env", [_entry("DB_PASSWORD", "")])
    result = score_file(parsed)
    assert result.empty_value_count == 1
    assert result.score >= 1


def test_score_file_capped_at_100():
    entries = [_entry(f"KEY_{i}", "a" * 40) for i in range(20)]
    parsed = _parsed(".env", entries)
    result = score_file(parsed)
    assert result.score <= 100


def test_score_file_returns_file_score_instance():
    parsed = _parsed(".env", [])
    result = score_file(parsed)
    assert isinstance(result, FileScore)
    assert result.path == ".env"


# ---------------------------------------------------------------------------
# score_many
# ---------------------------------------------------------------------------

def test_score_many_sorted_highest_first():
    clean = _parsed(".env.example", [_entry("APP", "val")])
    risky = _parsed(".env", [_entry("TOKEN", "b" * 40)])
    results = score_many([clean, risky])
    assert results[0].path == ".env"


def test_score_many_empty_list():
    assert score_many([]) == []
