"""Tests for dotenv_audit.tagger."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.tagger import (
    TaggedEnvFile,
    TaggedEntry,
    tag_entry,
    tag_env_file,
)


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", lineno=1)


def _parsed(*entries: EnvEntry, path: str = ".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=list(entries))


# --- tag_entry ---

def test_tag_entry_database_key():
    tags = tag_entry(_entry("DB_HOST"))
    assert "database" in tags


def test_tag_entry_auth_key():
    tags = tag_entry(_entry("JWT_SECRET"))
    assert "auth" in tags


def test_tag_entry_aws_key():
    tags = tag_entry(_entry("AWS_ACCESS_KEY_ID"))
    assert "aws" in tags


def test_tag_entry_email_key():
    tags = tag_entry(_entry("SMTP_HOST"))
    assert "email" in tags


def test_tag_entry_url_key():
    tags = tag_entry(_entry("BASE_URL"))
    assert "url" in tags


def test_tag_entry_feature_key():
    tags = tag_entry(_entry("FEATURE_DARK_MODE"))
    assert "feature" in tags


def test_tag_entry_logging_key():
    tags = tag_entry(_entry("LOG_LEVEL"))
    assert "logging" in tags


def test_tag_entry_untagged_key_returns_empty():
    tags = tag_entry(_entry("APP_NAME"))
    assert tags == []


def test_tag_entry_multiple_tags():
    # SENTRY_AUTH_TOKEN should match both auth and logging
    tags = tag_entry(_entry("SENTRY_AUTH_TOKEN"))
    assert "auth" in tags
    assert "logging" in tags


# --- TaggedEntry.__str__ ---

def test_tagged_entry_str_with_tags():
    te = TaggedEntry(entry=_entry("DB_HOST"), tags=["database"])
    assert str(te) == "DB_HOST [database]"


def test_tagged_entry_str_no_tags():
    te = TaggedEntry(entry=_entry("APP_NAME"), tags=[])
    assert str(te) == "APP_NAME [untagged]"


# --- TaggedEnvFile ---

def test_tag_env_file_produces_correct_count():
    parsed = _parsed(_entry("DB_URL"), _entry("APP_NAME"), _entry("AWS_SECRET_KEY"))
    tagged = tag_env_file(parsed)
    assert len(tagged.entries) == 3


def test_tag_env_file_source_matches_path():
    parsed = _parsed(_entry("X"), path=".env.production")
    tagged = tag_env_file(parsed)
    assert tagged.source == ".env.production"


def test_by_tag_filters_correctly():
    parsed = _parsed(_entry("DB_HOST"), _entry("SMTP_HOST"), _entry("DB_PASS"))
    tagged = tag_env_file(parsed)
    db_entries = tagged.by_tag("database")
    assert all("database" in e.tags for e in db_entries)


def test_all_tags_sorted_and_unique():
    parsed = _parsed(_entry("DB_HOST"), _entry("LOG_LEVEL"), _entry("DB_PASS"))
    tagged = tag_env_file(parsed)
    all_t = tagged.all_tags()
    assert all_t == sorted(set(all_t))


def test_summary_contains_source():
    parsed = _parsed(_entry("DB_HOST"), path=".env")
    tagged = tag_env_file(parsed)
    assert ".env" in tagged.summary()


def test_summary_lists_untagged():
    parsed = _parsed(_entry("APP_NAME"))
    tagged = tag_env_file(parsed)
    assert "untagged" in tagged.summary()
