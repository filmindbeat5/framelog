"""Tests for framelog.job_retry."""

import pytest

from framelog.job_status import RenderJob, RenderStatus
from framelog.job_retry import JobRetryManager, RetryPolicy


@pytest.fixture
def failed_job():
    job = RenderJob(
        job_id="job-001",
        scene="scene_A",
        frame_range=(1, 100),
        server="render-01",
    )
    job.status = RenderStatus.FAILED
    job.error_message = "Segmentation fault"
    return job


@pytest.fixture
def manager():
    return JobRetryManager(policy=RetryPolicy(max_attempts=3))


def test_can_retry_failed_job(manager, failed_job):
    assert manager.can_retry(failed_job) is True


def test_cannot_retry_completed_job(manager):
    job = RenderJob(job_id="job-002", scene="s", frame_range=(1, 10), server="srv")
    job.status = RenderStatus.COMPLETED
    assert manager.can_retry(job) is False


def test_cannot_retry_pending_job(manager):
    job = RenderJob(job_id="job-003", scene="s", frame_range=(1, 10), server="srv")
    assert manager.can_retry(job) is False


def test_retry_resets_status_to_pending(manager, failed_job):
    result = manager.retry(failed_job)
    assert result is True
    assert failed_job.status == RenderStatus.PENDING


def test_retry_clears_error_message(manager, failed_job):
    manager.retry(failed_job)
    assert failed_job.error_message is None


def test_retry_increments_attempt_count(manager, failed_job):
    manager.retry(failed_job)
    assert manager.attempts(failed_job) == 1
    failed_job.status = RenderStatus.FAILED
    manager.retry(failed_job)
    assert manager.attempts(failed_job) == 2


def test_last_error_preserved_after_retry(manager, failed_job):
    original_error = failed_job.error_message
    manager.retry(failed_job)
    assert manager.last_error(failed_job) == original_error


def test_cannot_retry_after_max_attempts(manager, failed_job):
    for _ in range(3):
        assert manager.retry(failed_job) is True
        failed_job.status = RenderStatus.FAILED
    assert manager.can_retry(failed_job) is False
    assert manager.retry(failed_job) is False


def test_exhausted_after_max_attempts(manager, failed_job):
    assert manager.exhausted(failed_job) is False
    for _ in range(3):
        manager.retry(failed_job)
        failed_job.status = RenderStatus.FAILED
    assert manager.exhausted(failed_job) is True


def test_not_exhausted_when_under_limit(manager, failed_job):
    manager.retry(failed_job)
    failed_job.status = RenderStatus.FAILED
    assert manager.exhausted(failed_job) is False


def test_default_policy_max_attempts():
    mgr = JobRetryManager()
    assert mgr.policy.max_attempts == 3
