"""Tests for dotenv_audit.profiler."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.profiler import EnvProfile, profile_env_file, profile_many


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str, comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1)


def _parsed(path: str, entries: list) -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=entries)


# ---------------------------------------------------------------------------
# EnvProfile properties
# ---------------------------------------------------------------------------

def test_empty_ratio_no_keys():
    pf = _parsed(".env", [])
    prof = profile_env_file(pf)
    assert prof.empty_ratio == 0.0


def test_empty_ratio_all_empty():
    entries = [_entry("A", ""), _entry("B", "")]
    prof = profile_env_file(_parsed(".env", entries))
    assert prof.empty_ratio == 1.0


def test_empty_ratio_partial():
    entries = [_entry("A", ""), _entry("B", "hello")]
    prof = profile_env_file(_parsed(".env", entries))
    assert prof.empty_ratio == pytest.approx(0.5)


def test_secret_ratio_no_secrets():
    entries = [_entry("NAME", "alice"), _entry("ENV", "production")]
    prof = profile_env_file(_parsed(".env", entries))
    assert prof.secret_ratio == 0.0


def test_secret_ratio_with_secret():
    # A 40-char hex string triggers the secret heuristic
    secret = "a" * 40
    entries = [_entry("TOKEN", secret), _entry("NAME", "alice")]
    prof = profile_env_file(_parsed(".env", entries))
    assert prof.secret_ratio == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# profile_env_file
# ---------------------------------------------------------------------------

def test_profile_counts_total_keys():
    entries = [_entry("A", "1"), _entry("B", "2"), _entry("C", "")]
    prof = profile_env_file(_parsed(".env", entries))
    assert prof.total_keys == 3


def test_profile_counts_empty_keys():
    entries = [_entry("A", ""), _entry("B", "val")]
    prof = profile_env_file(_parsed(".env", entries))
    assert prof.empty_keys == 1


def test_profile_path_preserved():
    pf = _parsed("/project/.env.test", [])
    prof = profile_env_file(pf)
    assert prof.path == "/project/.env.test"


def test_profile_summary_contains_path():
    pf = _parsed("/project/.env", [_entry("K", "v")])
    prof = profile_env_file(pf)
    assert "/project/.env" in prof.summary()


def test_profile_summary_contains_key_count():
    entries = [_entry("A", "1"), _entry("B", "2")]
    prof = profile_env_file(_parsed(".env", entries))
    assert "Keys" in prof.summary()
    assert "2" in prof.summary()


# ---------------------------------------------------------------------------
# profile_many
# ---------------------------------------------------------------------------

def test_profile_many_empty_list():
    assert profile_many([]) == []


def test_profile_many_sorted_by_path():
    files = [
        _parsed("/z/.env", []),
        _parsed("/a/.env", []),
        _parsed("/m/.env", []),
    ]
    profiles = profile_many(files)
    paths = [p.path for p in profiles]
    assert paths == sorted(paths)


def test_profile_many_returns_correct_count():
    files = [_parsed(f"/.env.{i}", []) for i in range(5)]
    assert len(profile_many(files)) == 5
