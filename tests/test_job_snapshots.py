"""Tests for framelog.job_snapshots."""

import pytest

from framelog.job_snapshots import JobSnapshot, JobSnapshotManager
from framelog.job_status import RenderJob, RenderStatus


@pytest.fixture
def manager() -> JobSnapshotManager:
    return JobSnapshotManager()


@pytest.fixture
def job() -> RenderJob:
    return RenderJob(job_id="snap-001", frame_start=1, frame_end=50, server="node-1")


# --- JobSnapshot.to_dict / from_dict ---

def test_snapshot_to_dict_keys(job):
    snap = JobSnapshot.capture(job)
    d = snap.to_dict()
    assert set(d.keys()) == {
        "job_id", "status", "server", "frame_start",
        "frame_end", "error_message", "captured_at",
    }


def test_snapshot_roundtrip(job):
    snap = JobSnapshot.capture(job)
    restored = JobSnapshot.from_dict(snap.to_dict())
    assert restored.job_id == snap.job_id
    assert restored.status == snap.status
    assert restored.captured_at == snap.captured_at


def test_snapshot_captures_current_status(job):
    job.start()
    snap = JobSnapshot.capture(job)
    assert snap.status == RenderStatus.RUNNING.value


# --- JobSnapshotManager ---

def test_history_empty_before_capture(manager, job):
    assert manager.history(job.job_id) == []


def test_latest_none_before_capture(manager, job):
    assert manager.latest(job.job_id) is None


def test_capture_returns_snapshot(manager, job):
    snap = manager.capture(job)
    assert isinstance(snap, JobSnapshot)
    assert snap.job_id == job.job_id


def test_history_grows_with_captures(manager, job):
    manager.capture(job)
    job.start()
    manager.capture(job)
    assert len(manager.history(job.job_id)) == 2


def test_latest_returns_most_recent(manager, job):
    manager.capture(job)
    job.start()
    manager.capture(job)
    latest = manager.latest(job.job_id)
    assert latest.status == RenderStatus.RUNNING.value


def test_diff_empty_when_single_snapshot(manager, job):
    manager.capture(job)
    assert manager.diff(job.job_id) == []


def test_diff_detects_status_change(manager, job):
    manager.capture(job)
    job.start()
    manager.capture(job)
    diffs = manager.diff(job.job_id)
    assert len(diffs) == 1
    assert "status" in diffs[0]["changes"]


def test_diff_no_entry_when_no_change(manager, job):
    manager.capture(job)
    manager.capture(job)  # same state
    assert manager.diff(job.job_id) == []


def test_clear_removes_history(manager, job):
    manager.capture(job)
    manager.clear(job.job_id)
    assert manager.history(job.job_id) == []
