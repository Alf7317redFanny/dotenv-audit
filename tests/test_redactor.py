"""Tests for dotenv_audit.redactor."""

from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.redactor import (
    RedactedEntry,
    RedactedEnvFile,
    _REDACTED,
    redact_entry,
    redact_file,
)


def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw_line=f"{key}={value}", line_number=1)


def _parsed(entries: list[EnvEntry], path: str = ".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=entries)


def test_redact_entry_plain_value_not_redacted():
    entry = _entry("APP_NAME", "myapp")
    result = redact_entry(entry)
    assert result.was_redacted is False
    assert result.display_value == "myapp"


def test_redact_entry_hex_token_is_redacted():
    entry = _entry("SECRET_KEY", "a3f1c9d2e4b56789abcdef0123456789abcdef01")
    result = redact_entry(entry)
    assert result.was_redacted is True
    assert result.display_value == _REDACTED
    assert result.original_value == "a3f1c9d2e4b56789abcdef0123456789abcdef01"


def test_redact_entry_aws_key_is_redacted():
    entry = _entry("AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    result = redact_entry(entry)
    assert result.was_redacted is True
    assert result.display_value == _REDACTED


def test_redact_entry_placeholder_not_redacted():
    entry = _entry("DATABASE_URL", "<your-db-url>")
    result = redact_entry(entry)
    assert result.was_redacted is False
    assert result.display_value == "<your-db-url>"


def test_redact_entry_empty_value_not_redacted():
    entry = _entry("OPTIONAL_VAR", "")
    result = redact_entry(entry)
    assert result.was_redacted is False


def test_redact_entry_str_representation():
    entry = _entry("APP_ENV", "production")
    result = redact_entry(entry)
    assert str(result) == "APP_ENV=production"


def test_redact_file_returns_redacted_env_file():
    entries = [
        _entry("APP_NAME", "myapp"),
        _entry("SECRET_KEY", "a3f1c9d2e4b56789abcdef0123456789abcdef01"),
        _entry("PORT", "8080"),
    ]
    parsed = _parsed(entries, path=".env")
    result = redact_file(parsed)
    assert isinstance(result, RedactedEnvFile)
    assert result.path == ".env"
    assert len(result.entries) == 3


def test_redact_file_redacted_keys():
    entries = [
        _entry("APP_NAME", "myapp"),
        _entry("SECRET_KEY", "a3f1c9d2e4b56789abcdef0123456789abcdef01"),
    ]
    result = redact_file(_parsed(entries))
    assert result.redacted_keys() == ["SECRET_KEY"]


def test_redact_file_lines_output():
    entries = [
        _entry("APP_NAME", "myapp"),
        _entry("SECRET_KEY", "a3f1c9d2e4b56789abcdef0123456789abcdef01"),
    ]
    result = redact_file(_parsed(entries))
    lines = result.lines()
    assert lines[0] == "APP_NAME=myapp"
    assert lines[1] == f"SECRET_KEY={_REDACTED}"


def test_redact_file_no_secrets_all_pass_through():
    entries = [
        _entry("DEBUG", "true"),
        _entry("LOG_LEVEL", "info"),
    ]
    result = redact_file(_parsed(entries))
    assert result.redacted_keys() == []
    assert result.lines() == ["DEBUG=true", "LOG_LEVEL=info"]
