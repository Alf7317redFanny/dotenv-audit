"""Tests for dotenv_audit.normalizer."""

from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.normalizer import (
    NormalizedEntry,
    NormalizedEnvFile,
    normalize_entry,
    normalize_file,
    _normalize_value,
)


def _entry(key: str, value: str, comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1)


def _parsed(*entries: EnvEntry, path: str = ".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=list(entries))


# --- _normalize_value ---

def test_normalize_value_plain():
    val, quoted = _normalize_value("hello")
    assert val == "hello"
    assert quoted is False


def test_normalize_value_double_quoted():
    val, quoted = _normalize_value('"hello world"')
    assert val == "hello world"
    assert quoted is True


def test_normalize_value_single_quoted():
    val, quoted = _normalize_value("'secret'")
    assert val == "secret"
    assert quoted is True


def test_normalize_value_trims_whitespace():
    val, quoted = _normalize_value("  trimmed  ")
    assert val == "trimmed"
    assert quoted is False


def test_normalize_value_empty_string():
    val, quoted = _normalize_value("")
    assert val == ""
    assert quoted is False


# --- normalize_entry ---

def test_normalize_entry_plain_value():
    e = normalize_entry(_entry("FOO", "bar"))
    assert e.normalized_value == "bar"
    assert e.was_quoted is False
    assert e.is_empty_alias is False


def test_normalize_entry_quoted_value():
    e = normalize_entry(_entry("FOO", '"bar"'))
    assert e.normalized_value == "bar"
    assert e.was_quoted is True


def test_normalize_entry_null_alias():
    e = normalize_entry(_entry("DB_PASS", "null"))
    assert e.is_empty_alias is True


def test_normalize_entry_none_alias_case_insensitive():
    e = normalize_entry(_entry("DB_PASS", "NONE"))
    assert e.is_empty_alias is True


def test_normalize_entry_undefined_alias():
    e = normalize_entry(_entry("API_KEY", "undefined"))
    assert e.is_empty_alias is True


def test_normalize_entry_real_value_not_alias():
    e = normalize_entry(_entry("API_KEY", "abc123"))
    assert e.is_empty_alias is False


# --- normalize_file ---

def test_normalize_file_keys():
    parsed = _parsed(_entry("A", "1"), _entry("B", "2"))
    nf = normalize_file(parsed)
    assert nf.keys == ["A", "B"]


def test_normalize_file_empty_alias_keys():
    parsed = _parsed(_entry("A", "none"), _entry("B", "real_value"))
    nf = normalize_file(parsed)
    assert nf.empty_alias_keys == ["A"]


def test_normalize_file_quoted_keys():
    parsed = _parsed(_entry("A", '"quoted"'), _entry("B", "plain"))
    nf = normalize_file(parsed)
    assert nf.quoted_keys == ["A"]


def test_normalize_file_source_preserved():
    parsed = _parsed(_entry("X", "y"))
    nf = normalize_file(parsed)
    assert nf.source is parsed
