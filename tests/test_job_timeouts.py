"""Tests for framelog.job_timeouts."""

from datetime import datetime, timedelta

import pytest

from framelog.job_status import RenderJob, RenderStatus
from framelog.job_timeouts import JobTimeoutManager, TimeoutEvent, TimeoutPolicy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job(
    job_id: str = "job-1",
    status: RenderStatus = RenderStatus.RUNNING,
    started_at: datetime | None = None,
    created_at: datetime | None = None,
) -> RenderJob:
    job = RenderJob(job_id=job_id, scene="scene.blend", server="srv-1", frame_range=(1, 10))
    job.status = status
    if started_at:
        job.started_at = started_at
    if created_at:
        job.created_at = created_at
    return job


@pytest.fixture
def policy() -> TimeoutPolicy:
    return TimeoutPolicy(max_running_seconds=60.0, max_pending_seconds=120.0)


@pytest.fixture
def manager(policy) -> JobTimeoutManager:
    return JobTimeoutManager(policy=policy)


# ---------------------------------------------------------------------------
# TimeoutPolicy defaults
# ---------------------------------------------------------------------------

def test_default_policy_values():
    p = TimeoutPolicy()
    assert p.max_running_seconds == 3600.0
    assert p.max_pending_seconds == 7200.0


# ---------------------------------------------------------------------------
# check_job — RUNNING
# ---------------------------------------------------------------------------

def test_running_job_within_limit_returns_none(manager):
    now = datetime.utcnow()
    job = _make_job(started_at=now - timedelta(seconds=30))
    assert manager.check_job(job, now=now) is None


def test_running_job_exceeds_limit_returns_event(manager):
    now = datetime.utcnow()
    job = _make_job(started_at=now - timedelta(seconds=90))
    event = manager.check_job(job, now=now)
    assert isinstance(event, TimeoutEvent)
    assert event.job_id == job.job_id
    assert event.status_at_timeout == RenderStatus.RUNNING
    assert event.elapsed_seconds > 60.0


# ---------------------------------------------------------------------------
# check_job — PENDING
# ---------------------------------------------------------------------------

def test_pending_job_exceeds_limit_returns_event(manager):
    now = datetime.utcnow()
    job = _make_job(status=RenderStatus.PENDING, created_at=now - timedelta(seconds=200))
    event = manager.check_job(job, now=now)
    assert event is not None
    assert event.status_at_timeout == RenderStatus.PENDING


def test_pending_job_within_limit_returns_none(manager):
    now = datetime.utcnow()
    job = _make_job(status=RenderStatus.PENDING, created_at=now - timedelta(seconds=50))
    assert manager.check_job(job, now=now) is None


# ---------------------------------------------------------------------------
# check_job — non-trackable statuses
# ---------------------------------------------------------------------------

def test_completed_job_returns_none(manager):
    now = datetime.utcnow()
    job = _make_job(status=RenderStatus.COMPLETED, started_at=now - timedelta(hours=5))
    assert manager.check_job(job, now=now) is None


# ---------------------------------------------------------------------------
# Suppression
# ---------------------------------------------------------------------------

def test_suppressed_job_returns_no_event(manager):
    now = datetime.utcnow()
    job = _make_job(started_at=now - timedelta(seconds=90))
    manager.suppress(job.job_id)
    assert manager.check_job(job, now=now) is None


def test_is_suppressed_reflects_state(manager):
    manager.suppress("abc")
    assert manager.is_suppressed("abc")
    assert not manager.is_suppressed("xyz")


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------

def test_scan_returns_only_timed_out_jobs(manager):
    now = datetime.utcnow()
    ok_job = _make_job(job_id="ok", started_at=now - timedelta(seconds=10))
    bad_job = _make_job(job_id="bad", started_at=now - timedelta(seconds=90))
    events = manager.scan([ok_job, bad_job], now=now)
    assert len(events) == 1
    assert events[0].job_id == "bad"


def test_scan_empty_list_returns_empty(manager):
    assert manager.scan([]) == []


# ---------------------------------------------------------------------------
# TimeoutEvent.to_dict
# ---------------------------------------------------------------------------

def test_timeout_event_to_dict_keys():
    event = TimeoutEvent(
        job_id="j1",
        status_at_timeout=RenderStatus.RUNNING,
        elapsed_seconds=75.5,
    )
    d = event.to_dict()
    assert set(d.keys()) == {"job_id", "status_at_timeout", "elapsed_seconds", "detected_at"}
    assert d["status_at_timeout"] == "running"
