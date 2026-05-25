"""Tests for framelog.job_quota."""

import pytest

from framelog.job_quota import JobQuotaManager, QuotaPolicy, QuotaViolation
from framelog.job_status import RenderJob, RenderStatus


def _make_job(
    job_id: str,
    server: str = "srv-1",
    status: RenderStatus = RenderStatus.RUNNING,
) -> RenderJob:
    job = RenderJob(job_id=job_id, scene="scene.blend", server=server, frame_range=(1, 10))
    job.status = status
    return job


@pytest.fixture
def policy() -> QuotaPolicy:
    return QuotaPolicy(global_max=5, per_server_max=2)


@pytest.fixture
def manager(policy: QuotaPolicy) -> JobQuotaManager:
    return JobQuotaManager(policy=policy)


# --- QuotaPolicy defaults ---

def test_default_policy_values():
    p = QuotaPolicy()
    assert p.global_max == 100
    assert p.per_server_max == 20


# --- check: no violation ---

def test_check_allows_job_within_limits(manager):
    job = _make_job("j1", server="srv-1", status=RenderStatus.PENDING)
    assert manager.check(job) is None


# --- record_start / global_usage ---

def test_record_start_increments_global(manager):
    job = _make_job("j1")
    manager.record_start(job)
    assert manager.global_usage() == 1


def test_record_start_increments_server(manager):
    job = _make_job("j1", server="srv-1")
    manager.record_start(job)
    assert manager.server_usage()["srv-1"] == 1


# --- global quota violation ---

def test_check_global_limit_exceeded(manager):
    for i in range(5):
        manager.record_start(_make_job(f"j{i}", server="srv-1"))
    new_job = _make_job("j99", server="srv-2", status=RenderStatus.PENDING)
    violation = manager.check(new_job)
    assert isinstance(violation, QuotaViolation)
    assert "Global limit" in violation.reason


# --- per-server quota violation ---

def test_check_server_limit_exceeded(manager):
    manager.record_start(_make_job("j1", server="srv-1"))
    manager.record_start(_make_job("j2", server="srv-1"))
    new_job = _make_job("j3", server="srv-1", status=RenderStatus.PENDING)
    violation = manager.check(new_job)
    assert isinstance(violation, QuotaViolation)
    assert "srv-1" in violation.reason


# --- record_finish ---

def test_record_finish_decrements_global(manager):
    job = _make_job("j1")
    manager.record_start(job)
    manager.record_finish(job)
    assert manager.global_usage() == 0


def test_record_finish_decrements_server(manager):
    job = _make_job("j1", server="srv-1")
    manager.record_start(job)
    manager.record_finish(job)
    assert manager.server_usage().get("srv-1", 0) == 0


def test_record_finish_never_goes_negative(manager):
    job = _make_job("j1")
    manager.record_finish(job)  # no prior start
    assert manager.global_usage() == 0


# --- rebuild ---

def test_rebuild_counts_running_jobs(manager):
    jobs = [
        _make_job("j1", server="srv-1", status=RenderStatus.RUNNING),
        _make_job("j2", server="srv-1", status=RenderStatus.RUNNING),
        _make_job("j3", server="srv-2", status=RenderStatus.COMPLETED),
        _make_job("j4", server="srv-2", status=RenderStatus.PENDING),
    ]
    manager.rebuild(jobs)
    assert manager.global_usage() == 2
    assert manager.server_usage()["srv-1"] == 2
    assert "srv-2" not in manager.server_usage()


# --- QuotaViolation.to_dict ---

def test_violation_to_dict():
    v = QuotaViolation(job_id="j1", server="srv-1", reason="over limit")
    d = v.to_dict()
    assert d["job_id"] == "j1"
    assert d["server"] == "srv-1"
    assert d["reason"] == "over limit"
