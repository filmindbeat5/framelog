"""Tests for framelog.job_progress."""
import pytest
from datetime import datetime

from framelog.job_status import RenderJob, RenderStatus
from framelog.job_progress import JobProgressManager, ProgressSnapshot


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def manager() -> JobProgressManager:
    return JobProgressManager()


@pytest.fixture()
def job() -> RenderJob:
    return RenderJob(
        job_id="job-001",
        scene="scene_A",
        frame_start=1,
        frame_end=100,
        server="render-01",
    )


# ---------------------------------------------------------------------------
# ProgressSnapshot.to_dict
# ---------------------------------------------------------------------------

def test_snapshot_to_dict_keys(job, manager):
    snap = manager.update(job, frames_done=50)
    d = snap.to_dict()
    assert set(d.keys()) == {"job_id", "percent", "frames_done", "frames_total", "message"}


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_calculates_percent(job, manager):
    snap = manager.update(job, frames_done=25)
    assert snap.percent == 25.0
    assert snap.frames_total == 100


def test_update_stores_message(job, manager):
    snap = manager.update(job, frames_done=10, message="processing")
    assert snap.message == "processing"


def test_update_full_completion(job, manager):
    snap = manager.update(job, frames_done=100)
    assert snap.percent == 100.0


def test_update_zero_frames_done(job, manager):
    snap = manager.update(job, frames_done=0)
    assert snap.percent == 0.0


def test_update_invalid_frames_raises(job, manager):
    with pytest.raises(ValueError):
        manager.update(job, frames_done=101)


def test_update_negative_frames_raises(job, manager):
    with pytest.raises(ValueError):
        manager.update(job, frames_done=-1)


# ---------------------------------------------------------------------------
# get / all_snapshots / clear
# ---------------------------------------------------------------------------

def test_get_returns_none_for_unknown(manager):
    assert manager.get("no-such-job") is None


def test_get_returns_latest_snapshot(job, manager):
    manager.update(job, frames_done=30)
    manager.update(job, frames_done=60)
    snap = manager.get(job.job_id)
    assert snap is not None
    assert snap.frames_done == 60


def test_all_snapshots_sorted(manager):
    for jid, end in [("job-z", 10), ("job-a", 20), ("job-m", 5)]:
        j = RenderJob(job_id=jid, scene="s", frame_start=1, frame_end=end, server="srv")
        manager.update(j, frames_done=1)
    ids = [s.job_id for s in manager.all_snapshots()]
    assert ids == sorted(ids)


def test_clear_removes_entry(job, manager):
    manager.update(job, frames_done=50)
    manager.clear(job.job_id)
    assert manager.get(job.job_id) is None


def test_clear_unknown_is_noop(manager):
    manager.clear("ghost-job")  # should not raise


# ---------------------------------------------------------------------------
# completed_jobs
# ---------------------------------------------------------------------------

def test_completed_jobs_returns_only_full(manager):
    j1 = RenderJob(job_id="j1", scene="s", frame_start=1, frame_end=10, server="srv")
    j2 = RenderJob(job_id="j2", scene="s", frame_start=1, frame_end=10, server="srv")
    manager.update(j1, frames_done=10)
    manager.update(j2, frames_done=5)
    completed = manager.completed_jobs()
    assert len(completed) == 1
    assert completed[0].job_id == "j1"
