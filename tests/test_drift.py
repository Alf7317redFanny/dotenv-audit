"""Tests for dotenv_audit.drift."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from dotenv_audit.drift import DriftReport, detect_drift


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _write_baseline(tmp_path: Path, data: dict) -> str:
    bp = tmp_path / ".env-baseline.json"
    bp.write_text(json.dumps(data))
    return str(bp)


# ---------------------------------------------------------------------------
# DriftReport unit tests
# ---------------------------------------------------------------------------

def test_drift_report_has_drift_false_when_empty():
    r = DriftReport(env_path=".env")
    assert not r.has_drift


def test_drift_report_has_drift_true_when_added():
    r = DriftReport(env_path=".env", added=["NEW_KEY"])
    assert r.has_drift


def test_drift_report_summary_no_drift():
    r = DriftReport(env_path=".env")
    assert r.summary() == "no drift"


def test_drift_report_summary_mixed():
    r = DriftReport(env_path=".env", added=["A"], removed=["B", "C"], changed=["D"])
    assert "+1 added" in r.summary()
    assert "-2 removed" in r.summary()
    assert "~1 changed" in r.summary()


# ---------------------------------------------------------------------------
# detect_drift integration tests
# ---------------------------------------------------------------------------

def test_detect_drift_no_drift(tmp_path):
    _write_env(tmp_path, ".env", "KEY=value\nOTHER=stuff\n")
    baseline = _write_baseline(tmp_path, {".env": {"KEY": "value", "OTHER": "stuff"}})
    reports = detect_drift(str(tmp_path), baseline)
    assert len(reports) == 1
    assert not reports[0].has_drift


def test_detect_drift_added_key(tmp_path):
    _write_env(tmp_path, ".env", "KEY=value\nNEW=extra\n")
    baseline = _write_baseline(tmp_path, {".env": {"KEY": "value"}})
    reports = detect_drift(str(tmp_path), baseline)
    assert "NEW" in reports[0].added


def test_detect_drift_removed_key(tmp_path):
    _write_env(tmp_path, ".env", "KEY=value\n")
    baseline = _write_baseline(tmp_path, {".env": {"KEY": "value", "OLD": "gone"}})
    reports = detect_drift(str(tmp_path), baseline)
    assert "OLD" in reports[0].removed


def test_detect_drift_changed_key(tmp_path):
    _write_env(tmp_path, ".env", "KEY=new_value\n")
    baseline = _write_baseline(tmp_path, {".env": {"KEY": "old_value"}})
    reports = detect_drift(str(tmp_path), baseline)
    assert "KEY" in reports[0].changed


def test_detect_drift_missing_from_baseline(tmp_path):
    _write_env(tmp_path, ".env", "KEY=value\n")
    baseline = _write_baseline(tmp_path, {})
    reports = detect_drift(str(tmp_path), baseline)
    assert "KEY" in reports[0].added
