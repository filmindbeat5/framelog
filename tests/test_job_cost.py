"""Tests for framelog.job_cost module."""

import pytest
from datetime import datetime, timedelta
from framelog.job_status import RenderJob
from framelog.job_cost import JobCostManager, JobCostEntry


def _make_job(job_id: str, server_id: str = "srv-1", duration_seconds: float = 60.0) -> RenderJob:
    job = RenderJob(job_id=job_id, scene_file="scene.blend", frame_range=(1, 100), server_id=server_id)
    job.started_at = datetime(2024, 1, 1, 12, 0, 0)
    job.finished_at = job.started_at + timedelta(seconds=duration_seconds)
    return job


@pytest.fixture
def manager() -> JobCostManager:
    return JobCostManager()


def test_default_rate_used_when_no_server_rate_set(manager):
    job = _make_job("j1", duration_seconds=100.0)
    entry = manager.calculate(job)
    assert entry is not None
    assert entry.cost_per_second == JobCostManager.DEFAULT_RATE
    assert abs(entry.estimated_cost - 100.0 * JobCostManager.DEFAULT_RATE) < 1e-9


def test_custom_rate_applied(manager):
    manager.set_rate("srv-1", 0.05)
    job = _make_job("j2", server_id="srv-1", duration_seconds=200.0)
    entry = manager.calculate(job)
    assert entry.cost_per_second == 0.05
    assert abs(entry.estimated_cost - 10.0) < 1e-9


def test_no_entry_when_no_started_at(manager):
    job = RenderJob(job_id="j3", scene_file="s.blend", frame_range=(1, 10), server_id="srv-1")
    job.finished_at = datetime(2024, 1, 1, 12, 0, 0)
    result = manager.calculate(job)
    assert result is None


def test_no_entry_when_no_finished_at(manager):
    job = RenderJob(job_id="j4", scene_file="s.blend", frame_range=(1, 10), server_id="srv-1")
    job.started_at = datetime(2024, 1, 1, 12, 0, 0)
    result = manager.calculate(job)
    assert result is None


def test_get_entry_returns_calculated(manager):
    job = _make_job("j5", duration_seconds=30.0)
    manager.calculate(job)
    entry = manager.get_entry("j5")
    assert isinstance(entry, JobCostEntry)
    assert entry.job_id == "j5"


def test_get_entry_returns_none_for_unknown(manager):
    assert manager.get_entry("nonexistent") is None


def test_total_cost_sums_all_entries(manager):
    manager.set_rate("srv-1", 0.02)
    manager.calculate(_make_job("j6", duration_seconds=50.0))
    manager.calculate(_make_job("j7", duration_seconds=50.0))
    assert abs(manager.total_cost() - 2.0) < 1e-6


def test_cost_by_server_groups_correctly(manager):
    manager.set_rate("srv-a", 0.10)
    manager.set_rate("srv-b", 0.20)
    manager.calculate(_make_job("j8", server_id="srv-a", duration_seconds=10.0))
    manager.calculate(_make_job("j9", server_id="srv-b", duration_seconds=10.0))
    manager.calculate(_make_job("j10", server_id="srv-a", duration_seconds=10.0))
    by_server = manager.cost_by_server()
    assert abs(by_server["srv-a"] - 2.0) < 1e-6
    assert abs(by_server["srv-b"] - 2.0) < 1e-6


def test_set_rate_negative_raises(manager):
    with pytest.raises(ValueError):
        manager.set_rate("srv-x", -0.01)


def test_entry_to_dict_keys(manager):
    job = _make_job("j11", duration_seconds=20.0)
    entry = manager.calculate(job)
    d = entry.to_dict()
    assert set(d.keys()) == {"job_id", "server_id", "duration_seconds", "cost_per_second", "estimated_cost"}
