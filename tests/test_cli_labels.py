"""Integration tests for framelog.cli_labels."""

import json
from pathlib import Path

import pytest

from framelog.cli_labels import build_parser, run_labels


@pytest.fixture()
def store(tmp_path) -> str:
    return str(tmp_path / "labels.json")


def _run(store: str, *argv: str) -> int:
    parser = build_parser()
    args = parser.parse_args(["--store", store, *argv])
    return run_labels(args)


def test_assign_creates_store(store):
    rc = _run(store, "assign", "job-1", "hero")
    assert rc == 0
    assert Path(store).exists()


def test_assign_persists_mapping(store):
    _run(store, "assign", "job-1", "hero")
    data = json.loads(Path(store).read_text())
    assert data["hero"] == "job-1"


def test_assign_conflict_returns_nonzero(store, capsys):
    _run(store, "assign", "job-1", "hero")
    rc = _run(store, "assign", "job-2", "hero")
    assert rc == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_unassign_removes_mapping(store):
    _run(store, "assign", "job-1", "hero")
    _run(store, "unassign", "hero")
    data = json.loads(Path(store).read_text())
    assert "hero" not in data


def test_resolve_prints_job_id(store, capsys):
    _run(store, "assign", "job-1", "hero")
    rc = _run(store, "resolve", "hero")
    assert rc == 0
    assert capsys.readouterr().out.strip() == "job-1"


def test_resolve_unknown_returns_nonzero(store, capsys):
    rc = _run(store, "resolve", "ghost")
    assert rc == 1
    assert "ghost" in capsys.readouterr().err


def test_list_all_labels(store, capsys):
    _run(store, "assign", "job-1", "alpha")
    _run(store, "assign", "job-2", "beta")
    _run(store, "list")
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_list_by_job(store, capsys):
    _run(store, "assign", "job-1", "alpha")
    _run(store, "assign", "job-1", "gamma")
    _run(store, "assign", "job-2", "beta")
    _run(store, "list", "--job", "job-1")
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "gamma" in out
    assert "beta" not in out
