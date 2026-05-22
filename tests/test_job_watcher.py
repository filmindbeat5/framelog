"""Tests for the JobWatcher module."""

import pytest
from framelog.job_status import RenderJob, RenderStatus
from framelog.job_watcher import JobWatcher, StateTransitionEvent


@pytest.fixture
def job() -> RenderJob:
    return RenderJob(job_id="job-001", server="render-01", frame_range=(1, 100))


@pytest.fixture
def watcher() -> JobWatcher:
    return JobWatcher()


def test_watch_records_job(watcher, job):
    watcher.watch(job)
    assert "job-001" in watcher.watched_job_ids


def test_no_event_when_status_unchanged(watcher, job):
    watcher.watch(job)
    events = watcher.check(job)
    assert events == []


def test_event_fired_on_status_change(watcher, job):
    watcher.watch(job)
    job.start()
    events = watcher.check(job)
    assert len(events) == 1
    assert events[0].new_status == RenderStatus.RUNNING
    assert events[0].previous_status == RenderStatus.PENDING


def test_handler_called_on_matching_transition(watcher, job):
    received: list = []
    watcher.on_transition(RenderStatus.RUNNING, lambda e: received.append(e))
    watcher.watch(job)
    job.start()
    watcher.check(job)
    assert len(received) == 1
    assert received[0].job_id == "job-001"


def test_wildcard_handler_called_on_any_transition(watcher, job):
    received: list = []
    watcher.on_transition(None, lambda e: received.append(e))
    watcher.watch(job)
    job.start()
    watcher.check(job)
    job.complete()
    watcher.check(job)
    assert len(received) == 2


def test_handler_not_called_for_different_status(watcher, job):
    received: list = []
    watcher.on_transition(RenderStatus.FAILED, lambda e: received.append(e))
    watcher.watch(job)
    job.start()
    watcher.check(job)
    assert received == []


def test_failed_event_includes_error_message(watcher, job):
    watcher.watch(job)
    job.start()
    watcher.check(job)
    job.fail("Out of memory")
    events = watcher.check(job)
    assert events[0].message == "Out of memory"
    assert events[0].new_status == RenderStatus.FAILED


def test_unwatch_removes_job(watcher, job):
    watcher.watch(job)
    watcher.unwatch(job.job_id)
    assert job.job_id not in watcher.watched_job_ids


def test_check_unwatched_job_treats_as_new(watcher, job):
    job.start()
    events = watcher.check(job)
    assert len(events) == 1
    assert events[0].previous_status is None
