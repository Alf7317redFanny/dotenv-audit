"""Tests for dotenv_audit.commands.validate_cmd."""
from __future__ import annotations

import argparse
import json
import os

import pytest

from dotenv_audit.commands.validate_cmd import cmd_validate, register


def _make_args(
    directory: str,
    schema: str,
    no_require_all: bool = False,
    verbose: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        directory=directory,
        schema=schema,
        no_require_all=no_require_all,
        verbose=verbose,
    )


def _write_env(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(content)


def _write_schema(path: str, schema: dict) -> None:
    with open(path, "w") as fh:
        json.dump(schema, fh)


def test_validate_cmd_returns_2_for_missing_directory(tmp_path):
    args = _make_args(str(tmp_path / "nope"), str(tmp_path / "schema.json"))
    assert cmd_validate(args) == 2


def test_validate_cmd_returns_2_for_missing_schema(tmp_path):
    args = _make_args(str(tmp_path), str(tmp_path / "missing.json"))
    assert cmd_validate(args) == 2


def test_validate_cmd_returns_2_for_invalid_json_schema(tmp_path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text("not json")
    args = _make_args(str(tmp_path), str(schema_path))
    assert cmd_validate(args) == 2


def test_validate_cmd_returns_0_when_no_files(tmp_path):
    schema_path = tmp_path / "schema.json"
    _write_schema(str(schema_path), {"PORT": "int"})
    args = _make_args(str(tmp_path), str(schema_path))
    assert cmd_validate(args) == 0


def test_validate_cmd_returns_0_for_valid_file(tmp_path):
    _write_env(str(tmp_path / ".env"), "PORT=8080\nDEBUG=true\n")
    schema_path = tmp_path / "schema.json"
    _write_schema(str(schema_path), {"PORT": "int", "DEBUG": "bool"})
    args = _make_args(str(tmp_path), str(schema_path))
    assert cmd_validate(args) == 0


def test_validate_cmd_returns_1_for_type_mismatch(tmp_path):
    _write_env(str(tmp_path / ".env"), "PORT=not-a-number\n")
    schema_path = tmp_path / "schema.json"
    _write_schema(str(schema_path), {"PORT": "int"})
    args = _make_args(str(tmp_path), str(schema_path), no_require_all=True)
    assert cmd_validate(args) == 1


def test_validate_cmd_returns_1_for_missing_required_key(tmp_path):
    _write_env(str(tmp_path / ".env"), "PORT=8080\n")
    schema_path = tmp_path / "schema.json"
    _write_schema(str(schema_path), {"PORT": "int", "SECRET_KEY": "str"})
    args = _make_args(str(tmp_path), str(schema_path))
    assert cmd_validate(args) == 1


def test_validate_cmd_no_require_all_ignores_missing(tmp_path):
    _write_env(str(tmp_path / ".env"), "PORT=8080\n")
    schema_path = tmp_path / "schema.json"
    _write_schema(str(schema_path), {"PORT": "int", "SECRET_KEY": "str"})
    args = _make_args(str(tmp_path), str(schema_path), no_require_all=True)
    assert cmd_validate(args) == 0


def test_register_adds_validate_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    parsed = parser.parse_args(["validate", ".", "--schema", "s.json"])
    assert parsed.directory == "."
    assert parsed.schema == "s.json"
