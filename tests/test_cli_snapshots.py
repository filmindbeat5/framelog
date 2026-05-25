"""Integration tests for cli_snapshots."""

import json
from pathlib import Path

import pytest

from framelog.cli_snapshots import build_parser, run_snapshots
from framelog.job_status import RenderJob, RenderStatus


@pytest.fixture
def jobs_file(tmp_path) -> Path:
    jobs = [
        {
            "job_id": "j1",
            "status": "pending",
            "server": "node-1",
            "frame_start": 1,
            "frame_end": 10,
            "error_message": None,
        },
        {
            "job_id": "j2",
            "status": "completed",
            "server": "node-2",
            "frame_start": 11,
            "frame_end": 20,
            "error_message": None,
        },
    ]
    p = tmp_path / "jobs.json"
    p.write_text(json.dumps(jobs))
    return p


@pytest.fixture
def snap_file(tmp_path, jobs_file) -> Path:
    out = tmp_path / "snaps.json"
    parser = build_parser()
    args = parser.parse_args(["capture", str(jobs_file), "--out", str(out)])
    run_snapshots(args)
    return out


def _run(args_list):
    parser = build_parser()
    args = parser.parse_args(args_list)
    return run_snapshots(args)


def test_capture_creates_file(tmp_path, jobs_file):
    out = tmp_path / "out.json"
    rc = _run(["capture", str(jobs_file), "--out", str(out)])
    assert rc == 0
    assert out.exists()


def test_capture_snapshot_count(tmp_path, jobs_file):
    out = tmp_path / "out.json"
    _run(["capture", str(jobs_file), "--out", str(out)])
    data = json.loads(out.read_text())
    assert len(data) == 2


def test_capture_snapshot_has_required_keys(tmp_path, jobs_file):
    out = tmp_path / "out.json"
    _run(["capture", str(jobs_file), "--out", str(out)])
    snap = json.loads(out.read_text())[0]
    assert "job_id" in snap and "status" in snap and "captured_at" in snap


def test_history_returns_zero_for_known_job(snap_file):
    rc = _run(["history", str(snap_file), "j1"])
    assert rc == 0


def test_history_returns_nonzero_for_unknown_job(snap_file):
    rc = _run(["history", str(snap_file), "unknown-job"])
    assert rc == 1


def test_diff_returns_zero_for_known_job(snap_file):
    # Single snapshot per job — no diffs, but exit 0
    rc = _run(["diff", str(snap_file), "j1"])
    assert rc == 0
