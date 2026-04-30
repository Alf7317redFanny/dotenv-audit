"""Tests for score_cmd.register and _dispatch integration."""
from __future__ import annotations

import argparse

import pytest

from dotenv_audit.commands.score_cmd import register, _dispatch


def _make_subparsers():
    root = argparse.ArgumentParser(prog="dotenv-audit")
    return root, root.add_subparsers(dest="command")


def test_register_adds_score_subcommand():
    root, subs = _make_subparsers()
    register(subs)
    args = root.parse_args(["score", "."])
    assert args.command == "score"
    assert args.directory == "."


def test_register_defaults_directory_to_dot():
    root, subs = _make_subparsers()
    register(subs)
    args = root.parse_args(["score"])
    assert args.directory == "."


def test_register_no_color_flag():
    root, subs = _make_subparsers()
    register(subs)
    args = root.parse_args(["score", "--no-color"])
    assert args.no_color is True


def test_dispatch_calls_cmd_score(tmp_path):
    args = argparse.Namespace(directory=str(tmp_path), no_color=True)
    rc = _dispatch(args)
    assert rc == 0


def test_dispatch_returns_2_for_bad_dir():
    args = argparse.Namespace(directory="/no/such/path", no_color=True)
    rc = _dispatch(args)
    assert rc == 2
