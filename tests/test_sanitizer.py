"""Tests for dotenv_audit.sanitizer."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.sanitizer import (
    SanitizeIssue,
    SanitizeResult,
    _sanitize_value,
    sanitize_env_file,
)


def _entry(key: str, value: str | None) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value or ''}", line_number=1)


def _parsed(*entries: EnvEntry, path: str = ".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=list(entries))


# --- _sanitize_value ---

def test_sanitize_value_plain_is_clean():
    val, reason = _sanitize_value("hello")
    assert val == "hello"
    assert reason is None


def test_sanitize_value_removes_control_characters():
    val, reason = _sanitize_value("hello\x00world")
    assert "\x00" not in val
    assert reason == "contains control characters"
    assert val == "helloworld"


def test_sanitize_value_removes_multiple_control_chars():
    val, reason = _sanitize_value("\x01ab\x1fcd")
    assert val == "abcd"
    assert reason is not None


def test_sanitize_value_unquoted_special_gets_quoted():
    val, reason = _sanitize_value("hello world")
    assert val == '"hello world"'
    assert reason == "unquoted value contains special shell characters"


def test_sanitize_value_already_double_quoted_is_clean():
    val, reason = _sanitize_value('"hello world"')
    assert reason is None
    assert val == '"hello world"'


def test_sanitize_value_already_single_quoted_is_clean():
    val, reason = _sanitize_value("'hello world'")
    assert reason is None


def test_sanitize_value_pipe_triggers_quote():
    val, reason = _sanitize_value("cmd|evil")
    assert reason is not None
    assert val == '"cmd|evil"'


# --- SanitizeResult ---

def test_sanitize_result_no_issues():
    r = SanitizeResult(source=".env")
    assert not r.has_issues
    assert "no sanitization" in r.summary()


def test_sanitize_result_has_issues():
    r = SanitizeResult(
        source=".env",
        issues=[SanitizeIssue(key="K", original="a\x00b", sanitized="ab", reason="control")],
    )
    assert r.has_issues
    assert "1 issue" in r.summary()


def test_sanitize_issue_str():
    issue = SanitizeIssue(key="FOO", original="a\x00", sanitized="a", reason="contains control characters")
    s = str(issue)
    assert "FOO" in s
    assert "contains control characters" in s


# --- sanitize_env_file ---

def test_sanitize_clean_file_no_issues():
    p = _parsed(_entry("KEY", "value"), _entry("OTHER", "123"))
    result = sanitize_env_file(p)
    assert not result.has_issues
    assert result.clean_lines == ["KEY=value", "OTHER=123"]


def test_sanitize_detects_control_char():
    p = _parsed(_entry("SECRET", "abc\x07def"))
    result = sanitize_env_file(p)
    assert result.has_issues
    assert result.issues[0].key == "SECRET"
    assert result.clean_lines == ["SECRET=abcdef"]


def test_sanitize_none_value_written_as_empty():
    p = _parsed(_entry("EMPTY", None))
    result = sanitize_env_file(p)
    assert not result.has_issues
    assert result.clean_lines == ["EMPTY="]


def test_sanitize_multiple_entries_partial_issues():
    p = _parsed(
        _entry("CLEAN", "ok"),
        _entry("DIRTY", "val ue"),
    )
    result = sanitize_env_file(p)
    assert len(result.issues) == 1
    assert result.issues[0].key == "DIRTY"
    assert result.clean_lines[0] == "CLEAN=ok"
