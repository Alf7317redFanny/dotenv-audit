"""Tests for dotenv_audit.interpolator."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.interpolator import (
    _extract_refs,
    interpolate_env_file,
    InterpolationIssue,
    InterpolationResult,
)


def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw_line=f"{key}={value}", line_number=1)


def _parsed(*entries: EnvEntry, path: str = ".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=list(entries))


# --- _extract_refs ---

def test_extract_refs_no_refs():
    assert _extract_refs("plain_value") == []


def test_extract_refs_single_ref():
    assert _extract_refs("${BASE_URL}/api") == ["BASE_URL"]


def test_extract_refs_multiple_refs():
    assert _extract_refs("${HOST}:${PORT}") == ["HOST", "PORT"]


def test_extract_refs_malformed_no_close():
    assert _extract_refs("${BROKEN") == []


# --- InterpolationResult ---

def test_interpolation_result_no_issues():
    result = InterpolationResult(file_path=".env")
    assert not result.has_issues


def test_interpolation_result_has_issues():
    result = InterpolationResult(
        file_path=".env",
        issues=[InterpolationIssue("KEY", "MISSING", "undefined")],
    )
    assert result.has_issues


def test_interpolation_result_summary_no_issues():
    result = InterpolationResult(file_path=".env")
    assert "no interpolation issues" in result.summary()


def test_interpolation_result_summary_with_issues():
    result = InterpolationResult(
        file_path=".env",
        issues=[InterpolationIssue("KEY", "MISSING", "undefined")],
    )
    summary = result.summary()
    assert "1 interpolation issue" in summary
    assert "undefined" in summary


def test_interpolation_issue_str():
    issue = InterpolationIssue("URL", "HOST", "undefined")
    assert str(issue) == "URL -> ${HOST}: undefined reference"


# --- interpolate_env_file ---

def test_no_interpolation_no_issues():
    parsed = _parsed(_entry("FOO", "bar"), _entry("BAZ", "qux"))
    result = interpolate_env_file(parsed)
    assert not result.has_issues
    assert result.resolved["FOO"] == "bar"


def test_resolves_simple_reference():
    parsed = _parsed(_entry("HOST", "localhost"), _entry("URL", "http://${HOST}/api"))
    result = interpolate_env_file(parsed)
    assert not result.has_issues
    assert result.resolved["URL"] == "http://localhost/api"


def test_detects_undefined_reference():
    parsed = _parsed(_entry("URL", "http://${HOST}/api"))
    result = interpolate_env_file(parsed)
    assert result.has_issues
    assert result.issues[0].ref == "HOST"
    assert result.issues[0].kind == "undefined"


def test_detects_circular_reference():
    parsed = _parsed(
        _entry("A", "${B}"),
        _entry("B", "${A}"),
    )
    result = interpolate_env_file(parsed)
    assert result.has_issues
    kinds = {i.kind for i in result.issues}
    assert "circular" in kinds


def test_multiple_refs_one_missing():
    parsed = _parsed(
        _entry("HOST", "localhost"),
        _entry("URL", "${HOST}:${PORT}"),
    )
    result = interpolate_env_file(parsed)
    assert result.has_issues
    assert any(i.ref == "PORT" for i in result.issues)


def test_empty_file_no_issues():
    parsed = _parsed(path=".env.empty")
    result = interpolate_env_file(parsed)
    assert not result.has_issues
    assert result.resolved == {}
