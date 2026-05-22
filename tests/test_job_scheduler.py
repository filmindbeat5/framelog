"""Tests for JobScheduler priority queue."""

import pytest

from framelog.job_scheduler import JobScheduler
from framelog.job_status import RenderJob, RenderStatus


@pytest.fixture
def scheduler() -> JobScheduler:
    return JobScheduler()


@pytest.fixture
def pending_job() -> RenderJob:
    return RenderJob(job_id="job-001", scene="scene_A", frame_range=(1, 100), server="render-01")


def test_enqueue_pending_job(scheduler, pending_job):
    scheduler.enqueue(pending_job, priority=5)
    assert scheduler.pending_count() == 1


def test_dequeue_returns_job(scheduler, pending_job):
    scheduler.enqueue(pending_job)
    result = scheduler.dequeue()
    assert result is pending_job


def test_dequeue_empty_returns_none(scheduler):
    assert scheduler.dequeue() is None


def test_priority_ordering(scheduler):
    low = RenderJob(job_id="low", scene="s", frame_range=(1, 10), server="srv")
    high = RenderJob(job_id="high", scene="s", frame_range=(1, 10), server="srv")
    scheduler.enqueue(low, priority=20)
    scheduler.enqueue(high, priority=1)
    first = scheduler.dequeue()
    assert first.job_id == "high"


def test_enqueue_duplicate_raises(scheduler, pending_job):
    scheduler.enqueue(pending_job)
    with pytest.raises(ValueError, match="already scheduled"):
        scheduler.enqueue(pending_job)


def test_enqueue_non_pending_raises(scheduler):
    job = RenderJob(job_id="j", scene="s", frame_range=(1, 1), server="srv")
    job.start()
    with pytest.raises(ValueError, match="Only PENDING"):
        scheduler.enqueue(job)


def test_remove_existing_job(scheduler, pending_job):
    scheduler.enqueue(pending_job)
    removed = scheduler.remove("job-001")
    assert removed is True
    assert scheduler.is_empty()


def test_remove_nonexistent_job(scheduler):
    assert scheduler.remove("ghost") is False


def test_peek_does_not_remove(scheduler, pending_job):
    scheduler.enqueue(pending_job)
    scheduler.peek()
    assert scheduler.pending_count() == 1


def test_all_scheduled_sorted(scheduler):
    for i, prio in enumerate([30, 10, 20]):
        j = RenderJob(job_id=f"j{i}", scene="s", frame_range=(1, 1), server="srv")
        scheduler.enqueue(j, priority=prio)
    ordered = scheduler.all_scheduled()
    priorities_seen = []
    for job in ordered:
        entry = next(e for e in scheduler._heap if e.job.job_id == job.job_id)
        priorities_seen.append(entry.priority)
    assert priorities_seen == sorted(priorities_seen)


def test_is_empty_initially(scheduler):
    assert scheduler.is_empty()
