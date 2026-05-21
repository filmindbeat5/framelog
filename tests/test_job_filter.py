"""Tests for framelog.job_filter filtering utilities."""

from datetime import datetime, timedelta

import pytest

from framelog.job_status import RenderJob, RenderStatus
from framelog.job_filter import (
    filter_by_status,
    filter_by_server,
    filter_by_time_range,
    filter_failed_with_message,
    group_by_status,
)


@pytest.fixture
def jobs():
    base_time = datetime(2024, 6, 1, 12, 0, 0)

    j1 = RenderJob(job_id="job-1", name="Scene A", server_id="srv-1")
    j1.created_at = base_time

    j2 = RenderJob(job_id="job-2", name="Scene B", server_id="srv-2")
    j2.created_at = base_time + timedelta(hours=1)
    j2.start()

    j3 = RenderJob(job_id="job-3", name="Scene C", server_id="srv-1")
    j3.created_at = base_time + timedelta(hours=2)
    j3.start()
    j3.complete()

    j4 = RenderJob(job_id="job-4", name="Scene D", server_id="srv-2")
    j4.created_at = base_time + timedelta(hours=3)
    j4.start()
    j4.fail("Out of memory error")

    j5 = RenderJob(job_id="job-5", name="Scene E", server_id="srv-1")
    j5.created_at = base_time + timedelta(hours=4)
    j5.start()
    j5.fail("Disk I/O timeout")

    return [j1, j2, j3, j4, j5]


def test_filter_by_status_pending(jobs):
    result = filter_by_status(jobs, RenderStatus.PENDING)
    assert len(result) == 1
    assert result[0].job_id == "job-1"


def test_filter_by_status_failed(jobs):
    result = filter_by_status(jobs, RenderStatus.FAILED)
    assert len(result) == 2
    assert {j.job_id for j in result} == {"job-4", "job-5"}


def test_filter_by_server(jobs):
    result = filter_by_server(jobs, "srv-1")
    assert len(result) == 3
    assert all(j.server_id == "srv-1" for j in result)


def test_filter_by_server_no_match(jobs):
    result = filter_by_server(jobs, "srv-99")
    assert result == []


def test_filter_by_time_range_start_only(jobs):
    cutoff = datetime(2024, 6, 1, 14, 0, 0)
    result = filter_by_time_range(jobs, start=cutoff)
    assert len(result) == 3


def test_filter_by_time_range_end_only(jobs):
    cutoff = datetime(2024, 6, 1, 13, 0, 0)
    result = filter_by_time_range(jobs, end=cutoff)
    assert len(result) == 2


def test_filter_by_time_range_both_bounds(jobs):
    start = datetime(2024, 6, 1, 13, 0, 0)
    end = datetime(2024, 6, 1, 15, 0, 0)
    result = filter_by_time_range(jobs, start=start, end=end)
    assert len(result) == 2
    assert {j.job_id for j in result} == {"job-3", "job-4"}


def test_filter_failed_with_message(jobs):
    result = filter_failed_with_message(jobs, "memory")
    assert len(result) == 1
    assert result[0].job_id == "job-4"


def test_filter_failed_with_message_case_insensitive(jobs):
    result = filter_failed_with_message(jobs, "TIMEOUT")
    assert len(result) == 1
    assert result[0].job_id == "job-5"


def test_group_by_status(jobs):
    groups = group_by_status(jobs)
    assert len(groups[RenderStatus.PENDING]) == 1
    assert len(groups[RenderStatus.RUNNING]) == 1
    assert len(groups[RenderStatus.COMPLETED]) == 1
    assert len(groups[RenderStatus.FAILED]) == 2
