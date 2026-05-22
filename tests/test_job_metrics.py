"""Tests for framelog.job_metrics."""

from datetime import datetime, timedelta

import pytest

from framelog.job_status import RenderJob, RenderStatus, start, complete, fail
from framelog.job_metrics import compute_metrics, ServerMetrics


def _make_job(
    job_id: str,
    server: str = "render-01",
    status: str = "pending",
    duration_seconds: float | None = None,
) -> RenderJob:
    job = RenderJob(job_id=job_id, scene="scene.blend", frame_range=(1, 10), server=server)
    if status in ("running", "completed", "failed"):
        start(job)
    if status == "completed":
        complete(job)
        if duration_seconds is not None and job.started_at is not None:
            job.completed_at = job.started_at + timedelta(seconds=duration_seconds)
    elif status == "failed":
        fail(job, "error")
    return job


@pytest.fixture
def mixed_jobs():
    return [
        _make_job("j1", server="render-01", status="completed", duration_seconds=30.0),
        _make_job("j2", server="render-01", status="completed", duration_seconds=50.0),
        _make_job("j3", server="render-01", status="failed"),
        _make_job("j4", server="render-02", status="completed", duration_seconds=20.0),
        _make_job("j5", server="render-02", status="pending"),
    ]


def test_total_jobs(mixed_jobs):
    metrics = compute_metrics(mixed_jobs)
    assert metrics.total_jobs == 5


def test_by_status_counts(mixed_jobs):
    metrics = compute_metrics(mixed_jobs)
    assert metrics.by_status[RenderStatus.COMPLETED.value] == 3
    assert metrics.by_status[RenderStatus.FAILED.value] == 1
    assert metrics.by_status[RenderStatus.PENDING.value] == 1


def test_by_server_keys(mixed_jobs):
    metrics = compute_metrics(mixed_jobs)
    assert "render-01" in metrics.by_server
    assert "render-02" in metrics.by_server


def test_server_totals(mixed_jobs):
    metrics = compute_metrics(mixed_jobs)
    assert metrics.by_server["render-01"].total == 3
    assert metrics.by_server["render-02"].total == 2


def test_server_completed_and_failed(mixed_jobs):
    metrics = compute_metrics(mixed_jobs)
    sm = metrics.by_server["render-01"]
    assert sm.completed == 2
    assert sm.failed == 1


def test_success_rate(mixed_jobs):
    metrics = compute_metrics(mixed_jobs)
    assert pytest.approx(metrics.by_server["render-01"].success_rate, rel=1e-3) == 2 / 3
    assert pytest.approx(metrics.by_server["render-02"].success_rate, rel=1e-3) == 0.5


def test_avg_duration_per_server(mixed_jobs):
    metrics = compute_metrics(mixed_jobs)
    assert pytest.approx(metrics.by_server["render-01"].avg_duration_seconds, rel=1e-3) == 40.0
    assert pytest.approx(metrics.by_server["render-02"].avg_duration_seconds, rel=1e-3) == 20.0


def test_overall_avg_duration(mixed_jobs):
    metrics = compute_metrics(mixed_jobs)
    # durations: 30, 50, 20 -> avg = 100/3
    assert pytest.approx(metrics.overall_avg_duration_seconds, rel=1e-3) == 100.0 / 3


def test_empty_jobs():
    metrics = compute_metrics([])
    assert metrics.total_jobs == 0
    assert metrics.by_status == {}
    assert metrics.by_server == {}
    assert metrics.overall_avg_duration_seconds is None


def test_no_duration_when_not_completed():
    jobs = [_make_job("j1", status="failed")]
    metrics = compute_metrics(jobs)
    assert metrics.overall_avg_duration_seconds is None
    sm = metrics.by_server["render-01"]
    assert sm.avg_duration_seconds is None
