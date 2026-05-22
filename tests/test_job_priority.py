"""Tests for framelog.job_priority."""

import pytest

from framelog.job_status import RenderJob
from framelog.job_priority import JobPriorityManager, Priority


@pytest.fixture
def manager() -> JobPriorityManager:
    return JobPriorityManager()


@pytest.fixture
def job_a() -> RenderJob:
    return RenderJob(job_id="job-a", scene="scene_a.blend", frame_range=(1, 10), server="srv-1")


@pytest.fixture
def job_b() -> RenderJob:
    return RenderJob(job_id="job-b", scene="scene_b.blend", frame_range=(1, 10), server="srv-2")


@pytest.fixture
def job_c() -> RenderJob:
    return RenderJob(job_id="job-c", scene="scene_c.blend", frame_range=(1, 10), server="srv-1")


def test_default_priority_is_normal(manager, job_a):
    assert manager.get_priority(job_a) == Priority.NORMAL


def test_set_and_get_priority(manager, job_a):
    manager.set_priority(job_a, Priority.HIGH)
    assert manager.get_priority(job_a) == Priority.HIGH


def test_remove_priority_reverts_to_normal(manager, job_a):
    manager.set_priority(job_a, Priority.CRITICAL)
    manager.remove_priority(job_a)
    assert manager.get_priority(job_a) == Priority.NORMAL


def test_sort_jobs_highest_first(manager, job_a, job_b, job_c):
    manager.set_priority(job_a, Priority.LOW)
    manager.set_priority(job_b, Priority.CRITICAL)
    manager.set_priority(job_c, Priority.NORMAL)
    sorted_jobs = manager.sort_jobs([job_a, job_b, job_c])
    assert sorted_jobs[0] == job_b
    assert sorted_jobs[-1] == job_a


def test_jobs_at_priority_filters_correctly(manager, job_a, job_b, job_c):
    manager.set_priority(job_a, Priority.HIGH)
    manager.set_priority(job_b, Priority.HIGH)
    manager.set_priority(job_c, Priority.LOW)
    result = manager.jobs_at_priority([job_a, job_b, job_c], Priority.HIGH)
    assert job_a in result
    assert job_b in result
    assert job_c not in result


def test_promote_increases_priority(manager, job_a):
    manager.set_priority(job_a, Priority.NORMAL)
    new_p = manager.promote(job_a)
    assert new_p == Priority.HIGH
    assert manager.get_priority(job_a) == Priority.HIGH


def test_promote_at_critical_returns_none(manager, job_a):
    manager.set_priority(job_a, Priority.CRITICAL)
    result = manager.promote(job_a)
    assert result is None
    assert manager.get_priority(job_a) == Priority.CRITICAL


def test_demote_decreases_priority(manager, job_b):
    manager.set_priority(job_b, Priority.HIGH)
    new_p = manager.demote(job_b)
    assert new_p == Priority.NORMAL
    assert manager.get_priority(job_b) == Priority.NORMAL


def test_demote_at_low_returns_none(manager, job_b):
    manager.set_priority(job_b, Priority.LOW)
    result = manager.demote(job_b)
    assert result is None
    assert manager.get_priority(job_b) == Priority.LOW
