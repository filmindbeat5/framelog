"""Tests for the JobRegistry module."""

import pytest

from framelog.job_registry import JobRegistry
from framelog.job_status import RenderJob, RenderStatus, start, complete, fail


@pytest.fixture
def registry():
    return JobRegistry()


@pytest.fixture
def sample_jobs():
    jobs = [
        RenderJob(job_id="job-001", scene="scene_A", server_id="server-1"),
        RenderJob(job_id="job-002", scene="scene_B", server_id="server-2"),
        RenderJob(job_id="job-003", scene="scene_C", server_id="server-1"),
    ]
    return jobs


def test_register_and_retrieve_job(registry, sample_jobs):
    registry.register(sample_jobs[0])
    retrieved = registry.get("job-001")
    assert retrieved is sample_jobs[0]


def test_register_duplicate_raises(registry, sample_jobs):
    registry.register(sample_jobs[0])
    with pytest.raises(ValueError, match="already registered"):
        registry.register(sample_jobs[0])


def test_get_nonexistent_returns_none(registry):
    assert registry.get("nonexistent") is None


def test_all_jobs_returns_all(registry, sample_jobs):
    for job in sample_jobs:
        registry.register(job)
    assert len(registry.all_jobs()) == 3


def test_jobs_by_status_filters_correctly(registry, sample_jobs):
    registry.register(sample_jobs[0])
    registry.register(sample_jobs[1])
    registry.register(sample_jobs[2])

    start(sample_jobs[0])
    complete(sample_jobs[0])
    start(sample_jobs[1])
    fail(sample_jobs[1], "Out of memory")

    completed = registry.jobs_by_status(RenderStatus.COMPLETED)
    failed = registry.jobs_by_status(RenderStatus.FAILED)
    pending = registry.jobs_by_status(RenderStatus.PENDING)

    assert len(completed) == 1
    assert len(failed) == 1
    assert len(pending) == 1


def test_jobs_by_server_filters_correctly(registry, sample_jobs):
    for job in sample_jobs:
        registry.register(job)

    server1_jobs = registry.jobs_by_server("server-1")
    server2_jobs = registry.jobs_by_server("server-2")

    assert len(server1_jobs) == 2
    assert len(server2_jobs) == 1


def test_summary_counts_by_status(registry, sample_jobs):
    for job in sample_jobs:
        registry.register(job)
    start(sample_jobs[0])

    summary = registry.summary()
    assert summary[RenderStatus.PENDING.value] == 2
    assert summary[RenderStatus.RUNNING.value] == 1


def test_remove_job(registry, sample_jobs):
    registry.register(sample_jobs[0])
    registry.remove("job-001")
    assert registry.get("job-001") is None


def test_remove_nonexistent_raises(registry):
    with pytest.raises(KeyError, match="not found"):
        registry.remove("ghost-job")


def test_contains_operator(registry, sample_jobs):
    registry.register(sample_jobs[0])
    assert "job-001" in registry
    assert "job-999" not in registry


def test_len_reflects_job_count(registry, sample_jobs):
    assert len(registry) == 0
    for job in sample_jobs:
        registry.register(job)
    assert len(registry) == 3


def test_clear_removes_all_jobs(registry, sample_jobs):
    for job in sample_jobs:
        registry.register(job)
    registry.clear()
    assert len(registry) == 0
