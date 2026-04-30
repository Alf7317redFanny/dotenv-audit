"""Tests for dotenv_audit.templater."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.templater import (
    EnvTemplate,
    TemplateEntry,
    build_template,
    build_templates,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str = "", flag: str | None = None) -> EnvEntry:
    return EnvEntry(key=key, value=value, flag=flag)


def _parsed(path: str, *entries: EnvEntry) -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=list(entries))


# ---------------------------------------------------------------------------
# TemplateEntry
# ---------------------------------------------------------------------------

def test_template_entry_no_comment():
    te = TemplateEntry(key="DB_HOST")
    assert str(te) == "DB_HOST="


def test_template_entry_with_comment():
    te = TemplateEntry(key="API_KEY", comment="secret (hex_token)")
    result = str(te)
    assert result.startswith("# secret")
    assert "API_KEY=" in result


# ---------------------------------------------------------------------------
# EnvTemplate
# ---------------------------------------------------------------------------

def test_env_template_key_count():
    tmpl = EnvTemplate(
        source_path=".env",
        entries=[TemplateEntry("A"), TemplateEntry("B"), TemplateEntry("C")],
    )
    assert tmpl.key_count == 3


def test_env_template_render_contains_all_keys():
    tmpl = EnvTemplate(
        source_path=".env",
        entries=[TemplateEntry("FOO"), TemplateEntry("BAR")],
    )
    rendered = tmpl.render()
    assert "FOO=" in rendered
    assert "BAR=" in rendered


def test_env_template_lines_returns_list():
    tmpl = EnvTemplate(
        source_path=".env",
        entries=[TemplateEntry("X")],
    )
    assert isinstance(tmpl.lines(), list)
    assert len(tmpl.lines()) == 1


# ---------------------------------------------------------------------------
# build_template
# ---------------------------------------------------------------------------

def test_build_template_plain_values_no_comment():
    parsed = _parsed(".env", _entry("HOST", "localhost"), _entry("PORT", "5432"))
    tmpl = build_template(parsed)
    for entry in tmpl.entries:
        assert entry.comment == ""


def test_build_template_secret_entry_gets_comment():
    parsed = _parsed(".env", _entry("TOKEN", "abc123def456", flag="hex_token"))
    tmpl = build_template(parsed, annotate_secrets=True)
    assert tmpl.entries[0].comment != ""
    assert "hex_token" in tmpl.entries[0].comment


def test_build_template_annotate_false_suppresses_comment():
    parsed = _parsed(".env", _entry("TOKEN", "abc123def456", flag="hex_token"))
    tmpl = build_template(parsed, annotate_secrets=False)
    assert tmpl.entries[0].comment == ""


def test_build_template_preserves_key_order():
    keys = ["ALPHA", "BETA", "GAMMA"]
    parsed = _parsed(".env", *[_entry(k) for k in keys])
    tmpl = build_template(parsed)
    assert [e.key for e in tmpl.entries] == keys


def test_build_template_source_path():
    parsed = _parsed("/project/.env.production", _entry("KEY", "val"))
    tmpl = build_template(parsed)
    assert tmpl.source_path == "/project/.env.production"


# ---------------------------------------------------------------------------
# build_templates
# ---------------------------------------------------------------------------

def test_build_templates_returns_one_per_file():
    files = [
        _parsed(".env", _entry("A")),
        _parsed(".env.staging", _entry("B")),
    ]
    templates = build_templates(files)
    assert len(templates) == 2


def test_build_templates_empty_list():
    assert build_templates([]) == []
