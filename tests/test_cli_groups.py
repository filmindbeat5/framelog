"""Integration tests for framelog.cli_groups."""

import json
from pathlib import Path

import pytest

from framelog.cli_groups import build_parser, run_groups


@pytest.fixture()
def store(tmp_path) -> str:
    return str(tmp_path / "groups.json")


def _run(store: str, *args: str) -> int:
    parser = build_parser()
    ns = parser.parse_args(["--store", store, *args])
    return run_groups(ns)


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

def test_add_creates_store(store):
    rc = _run(store, "add", "--job", "j1", "--group", "vfx")
    assert rc == 0
    assert Path(store).exists()


def test_add_persists_membership(store):
    _run(store, "add", "--job", "j1", "--group", "vfx")
    data = json.loads(Path(store).read_text())
    assert "j1" in data["vfx"]


def test_add_multiple_jobs_to_group(store):
    _run(store, "add", "--job", "j1", "--group", "batch")
    _run(store, "add", "--job", "j2", "--group", "batch")
    data = json.loads(Path(store).read_text())
    assert set(data["batch"]) == {"j1", "j2"}


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------

def test_remove_updates_store(store):
    _run(store, "add", "--job", "j1", "--group", "vfx")
    rc = _run(store, "remove", "--job", "j1", "--group", "vfx")
    assert rc == 0
    data = json.loads(Path(store).read_text())
    assert "vfx" not in data or "j1" not in data.get("vfx", [])


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_prints_members(store, capsys):
    _run(store, "add", "--job", "j1", "--group", "vfx")
    _run(store, "add", "--job", "j2", "--group", "vfx")
    _run(store, "list", "--group", "vfx")
    out = capsys.readouterr().out
    assert "j1" in out
    assert "j2" in out


def test_list_empty_group(store, capsys):
    _run(store, "list", "--group", "ghost")
    out = capsys.readouterr().out
    assert "empty" in out or "does not exist" in out


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

def test_show_groups_for_job(store, capsys):
    _run(store, "add", "--job", "j1", "--group", "alpha")
    _run(store, "add", "--job", "j1", "--group", "beta")
    _run(store, "show", "--job", "j1")
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_show_no_groups(store, capsys):
    _run(store, "show", "--job", "unknown")
    out = capsys.readouterr().out
    assert "not in any group" in out


# ---------------------------------------------------------------------------
# disband
# ---------------------------------------------------------------------------

def test_disband_removes_group(store):
    _run(store, "add", "--job", "j1", "--group", "temp")
    rc = _run(store, "disband", "--group", "temp")
    assert rc == 0
    data = json.loads(Path(store).read_text())
    assert "temp" not in data
