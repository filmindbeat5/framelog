"""Tests for framelog.job_reporter."""

import pytest
from datetime import datetime

from framelog.job_status import RenderJob, RenderStatus, start, complete, fail
from framelog.job_registry import JobRegistry
from framelog.job_reporter import generate_report, format_report, JobReport


@pytest.fixture
def populated_registry():
    registry = JobRegistry()
    jobs = [
        RenderJob(job_id="job-001", server_id="server-a", frame_range=(1, 10)),
        RenderJob(job_id="job-002", server_id="server-a", frame_range=(11, 20)),
        RenderJob(job_id="job-003", server_id="server-b", frame_range=(1, 5)),
        RenderJob(job_id="job-004", server_id="server-b", frame_range=(6, 10)),
        RenderJob(job_id="job-005", server_id="server-c", frame_range=(1, 100)),
    ]
    start(jobs[0])
    complete(jobs[0])
    start(jobs[1])
    fail(jobs[1], "Out of memory")
    start(jobs[2])
    for job in jobs:
        registry.register(job)
    return registry


def test_report_total(populated_registry):
    report = generate_report(populated_registry)
    assert report.total == 5


def test_report_by_status_counts(populated_registry):
    report = generate_report(populated_registry)
    assert report.by_status.get(RenderStatus.COMPLETED.value) == 1
    assert report.by_status.get(RenderStatus.FAILED.value) == 1
    assert report.by_status.get(RenderStatus.RUNNING.value) == 1
    assert report.by_status.get(RenderStatus.PENDING.value) == 2


def test_report_by_server(populated_registry):
    report = generate_report(populated_registry)
    assert report.by_server["server-a"] == 2
    assert report.by_server["server-b"] == 2
    assert report.by_server["server-c"] == 1


def test_report_failed_messages(populated_registry):
    report = generate_report(populated_registry)
    assert len(report.failed_messages) == 1
    assert "Out of memory" in report.failed_messages[0]
    assert "job-002" in report.failed_messages[0]


def test_report_with_server_filter(populated_registry):
    report = generate_report(populated_registry, server="server-a")
    assert report.total == 2
    assert report.server_filter == "server-a"
    assert "server-b" not in report.by_server


def test_report_server_filter_no_match(populated_registry):
    report = generate_report(populated_registry, server="server-z")
    assert report.total == 0
    assert report.by_status == {}


def test_summary_line(populated_registry):
    report = generate_report(populated_registry)
    line = report.summary_line()
    assert "Total: 5" in line


def test_format_report_contains_sections(populated_registry):
    report = generate_report(populated_registry)
    output = format_report(report)
    assert "Render Job Report" in output
    assert "Status breakdown" in output
    assert "Jobs per server" in output
    assert "Failed job errors" in output
    assert "Out of memory" in output


def test_format_report_no_failures():
    registry = JobRegistry()
    job = RenderJob(job_id="j1", server_id="srv", frame_range=(1, 10))
    registry.register(job)
    report = generate_report(registry)
    output = format_report(report)
    assert "Failed job errors" not in output


def test_report_generated_at_is_datetime(populated_registry):
    report = generate_report(populated_registry)
    assert isinstance(report.generated_at, datetime)
