"""Tests for JobDispatcher."""

import pytest

from framelog.job_dispatcher import JobDispatcher
from framelog.job_registry import JobRegistry
from framelog.job_scheduler import JobScheduler
from framelog.job_status import RenderJob, RenderStatus


def _make_job(job_id: str) -> RenderJob:
    return RenderJob(job_id=job_id, scene="scene", frame_range=(1, 50), server="srv")


@pytest.fixture
def setup():
    scheduler = JobScheduler()
    registry = JobRegistry()
    dispatcher = JobDispatcher(scheduler, registry)
    return dispatcher, scheduler, registry


def test_dispatch_next_no_servers(setup):
    dispatcher, scheduler, _ = setup
    job = _make_job("j1")
    scheduler.enqueue(job)
    result = dispatcher.dispatch_next()
    assert result is None


def test_dispatch_next_no_jobs(setup):
    dispatcher, _, _ = setup
    dispatcher.register_server("render-01")
    result = dispatcher.dispatch_next()
    assert result is None


def test_dispatch_sets_running_status(setup):
    dispatcher, scheduler, _ = setup
    dispatcher.register_server("render-01")
    job = _make_job("j2")
    scheduler.enqueue(job)
    result = dispatcher.dispatch_next()
    assert result is not None
    assert result.success is True
    assert job.status == RenderStatus.RUNNING


def test_dispatch_records_history(setup):
    dispatcher, scheduler, _ = setup
    dispatcher.register_server("render-01")
    job = _make_job("j3")
    scheduler.enqueue(job)
    dispatcher.dispatch_next()
    assert len(dispatcher.history()) == 1


def test_failed_handler_marks_result(setup):
    dispatcher, scheduler, registry = setup
    dispatcher.register_server("render-01")

    def bad_handler(job, server):
        raise RuntimeError("connection refused")

    dispatcher._handler = bad_handler
    job = _make_job("j4")
    scheduler.enqueue(job)
    result = dispatcher.dispatch_next()
    assert result.success is False
    assert "connection refused" in result.error


def test_dispatch_all_drains_queue(setup):
    dispatcher, scheduler, _ = setup
    dispatcher.register_server("render-01")
    for i in range(4):
        scheduler.enqueue(_make_job(f"jx{i}"), priority=i)
    results = dispatcher.dispatch_all()
    assert len(results) == 4
    assert scheduler.is_empty()


def test_unregister_server_stops_dispatch(setup):
    dispatcher, scheduler, _ = setup
    dispatcher.register_server("render-01")
    dispatcher.unregister_server("render-01")
    scheduler.enqueue(_make_job("j5"))
    result = dispatcher.dispatch_next()
    assert result is None


def test_custom_handler_called(setup):
    dispatcher, scheduler, _ = setup
    dispatcher.register_server("render-01")
    called_with = []

    def capture(job, server):
        called_with.append((job.job_id, server))
        return True

    dispatcher._handler = capture
    job = _make_job("j6")
    scheduler.enqueue(job)
    dispatcher.dispatch_next()
    assert called_with == [("j6", "render-01")]
