"""Tests for framelog.job_exporter."""

import json
import csv
import io
import pytest

from framelog.job_status import RenderJob, RenderStatus, start, complete, fail
from framelog.job_registry import JobRegistry
from framelog.job_reporter import generate_report
from framelog.job_exporter import (
    export_jobs_to_json,
    export_jobs_to_csv,
    export_report_to_json,
    jobs_to_dict_list,
)


@pytest.fixture
def sample_jobs():
    j1 = RenderJob(job_id="j1", server_id="srv-1", frame_range=(1, 24))
    j2 = RenderJob(job_id="j2", server_id="srv-2", frame_range=(25, 48))
    j3 = RenderJob(job_id="j3", server_id="srv-1", frame_range=(49, 72))
    start(j1)
    complete(j1)
    start(j2)
    fail(j2, "GPU timeout")
    return [j1, j2, j3]


def test_jobs_to_dict_list_keys(sample_jobs):
    result = jobs_to_dict_list(sample_jobs)
    assert len(result) == 3
    expected_keys = {"job_id", "server_id", "status", "frame_start", "frame_end",
                     "created_at", "started_at", "completed_at", "error_message"}
    assert set(result[0].keys()) == expected_keys


def test_jobs_to_dict_list_status_values(sample_jobs):
    result = jobs_to_dict_list(sample_jobs)
    assert result[0]["status"] == RenderStatus.COMPLETED.value
    assert result[1]["status"] == RenderStatus.FAILED.value
    assert result[2]["status"] == RenderStatus.PENDING.value


def test_export_jobs_to_json_valid(sample_jobs):
    output = export_jobs_to_json(sample_jobs)
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 3
    assert parsed[1]["error_message"] == "GPU timeout"


def test_export_jobs_to_json_frame_range(sample_jobs):
    parsed = json.loads(export_jobs_to_json(sample_jobs))
    assert parsed[0]["frame_start"] == 1
    assert parsed[0]["frame_end"] == 24


def test_export_jobs_to_csv_has_header(sample_jobs):
    output = export_jobs_to_csv(sample_jobs)
    assert "job_id" in output
    assert "server_id" in output
    assert "error_message" in output


def test_export_jobs_to_csv_row_count(sample_jobs):
    output = export_jobs_to_csv(sample_jobs)
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 3


def test_export_jobs_to_csv_values(sample_jobs):
    output = export_jobs_to_csv(sample_jobs)
    reader = csv.DictReader(io.StringIO(output))
    rows = {r["job_id"]: r for r in reader}
    assert rows["j2"]["error_message"] == "GPU timeout"
    assert rows["j1"]["status"] == RenderStatus.COMPLETED.value


def test_export_report_to_json():
    registry = JobRegistry()
    j = RenderJob(job_id="j1", server_id="srv", frame_range=(1, 10))
    start(j)
    fail(j, "crash")
    registry.register(j)
    report = generate_report(registry)
    output = export_report_to_json(report)
    parsed = json.loads(output)
    assert parsed["total"] == 1
    assert RenderStatus.FAILED.value in parsed["by_status"]
    assert len(parsed["failed_messages"]) == 1
