"""Tests for dotenv_audit.rotator."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from dotenv_audit.rotator import (
    RotationEntry,
    RotationReport,
    _parse_timestamp,
    check_rotation,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str = "somevalue") -> MagicMock:
    e = MagicMock()
    e.key = key
    e.value = value
    return e


def _parsed(path: str, entries) -> MagicMock:
    p = MagicMock()
    p.path = path
    p.entries = entries
    return p


NOW = datetime.now(tz=timezone.utc)
OLD = NOW - timedelta(days=120)
FRESH = NOW - timedelta(days=10)


# ---------------------------------------------------------------------------
# _parse_timestamp
# ---------------------------------------------------------------------------

def test_parse_timestamp_valid_datetime():
    result = _parse_timestamp("2023-06-15T12:00:00")
    assert result is not None
    assert result.year == 2023


def test_parse_timestamp_valid_date_only():
    result = _parse_timestamp("2024-01-01")
    assert result is not None
    assert result.month == 1


def test_parse_timestamp_invalid_returns_none():
    assert _parse_timestamp("not-a-date") is None
    assert _parse_timestamp("") is None


# ---------------------------------------------------------------------------
# RotationEntry.__str__
# ---------------------------------------------------------------------------

def test_rotation_entry_str_with_timestamp():
    entry = RotationEntry("API_KEY", "abc", FRESH, False, "age 10d ok")
    s = str(entry)
    assert "API_KEY" in s
    assert "stale=False" in s


def test_rotation_entry_str_no_timestamp():
    entry = RotationEntry("SECRET", "xyz", None, True, "no rotation record found")
    s = str(entry)
    assert "unknown" in s
    assert "stale=True" in s


# ---------------------------------------------------------------------------
# RotationReport
# ---------------------------------------------------------------------------

def test_rotation_report_no_entries_has_no_stale():
    report = RotationReport(source=".env")
    assert not report.has_stale
    assert report.stale_keys == []


def test_rotation_report_detects_stale():
    e = RotationEntry("DB_PASS", "secret", OLD, True, "age 120d > 90d limit")
    report = RotationReport(source=".env", entries=[e])
    assert report.has_stale
    assert "DB_PASS" in report.stale_keys


def test_rotation_report_summary_no_entries():
    report = RotationReport(source=".env")
    assert "no tracked keys" in report.summary()


def test_rotation_report_summary_all_fresh():
    e = RotationEntry("TOKEN", "val", FRESH, False, "age 10d ok")
    report = RotationReport(source=".env", entries=[e])
    assert "up-to-date" in report.summary()


def test_rotation_report_summary_has_stale():
    e = RotationEntry("OLD_KEY", "val", OLD, True, "age 120d > 90d limit")
    report = RotationReport(source=".env", entries=[e])
    assert "stale" in report.summary()
    assert "OLD_KEY" in report.summary()


# ---------------------------------------------------------------------------
# check_rotation
# ---------------------------------------------------------------------------

def test_check_rotation_missing_from_map_is_stale():
    parsed = _parsed(".env", [_entry("API_KEY")])
    report = check_rotation(parsed, rotation_map={}, max_age_days=90)
    assert report.has_stale
    assert report.stale_keys == ["API_KEY"]


def test_check_rotation_fresh_key_not_stale():
    parsed = _parsed(".env", [_entry("API_KEY")])
    report = check_rotation(parsed, rotation_map={"API_KEY": FRESH}, max_age_days=90)
    assert not report.has_stale


def test_check_rotation_old_key_is_stale():
    parsed = _parsed(".env", [_entry("API_KEY")])
    report = check_rotation(parsed, rotation_map={"API_KEY": OLD}, max_age_days=90)
    assert report.has_stale


def test_check_rotation_skips_empty_values():
    parsed = _parsed(".env", [_entry("EMPTY_KEY", value="")])
    report = check_rotation(parsed, rotation_map={}, max_age_days=90)
    assert report.entries == []


def test_check_rotation_source_matches_path():
    parsed = _parsed("configs/.env.prod", [_entry("X")])
    report = check_rotation(parsed, rotation_map={}, max_age_days=30)
    assert report.source == "configs/.env.prod"
