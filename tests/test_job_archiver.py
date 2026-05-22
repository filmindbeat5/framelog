"""Tests for framelog.job_archiver."""

import json
import os

import pytest

from framelog.job_status import RenderJob, RenderStatus, start, complete, fail
from framelog.job_archiver import archive_jobs, load_archive


@pytest.fixture()
def jobs():
    j1 = RenderJob("job-1", "render-01", frame_range=range(1, 11))
    start(j1)
    complete(j1)

    j2 = RenderJob("job-2", "render-02", frame_range=range(11, 21))
    start(j2)
    fail(j2, "Out of memory")

    j3 = RenderJob("job-3", "render-01")
    return [j1, j2, j3]


def test_archive_creates_file(tmp_path, jobs):
    path = archive_jobs(jobs, archive_dir=str(tmp_path), label="test")
    assert os.path.isfile(path)


def test_archive_contains_all_jobs_by_default(tmp_path, jobs):
    path = archive_jobs(jobs, archive_dir=str(tmp_path))
    records = load_archive(path)
    assert len(records) == 3


def test_archive_filters_by_status(tmp_path, jobs):
    path = archive_jobs(
        jobs,
        archive_dir=str(tmp_path),
        statuses=[RenderStatus.FAILED],
    )
    records = load_archive(path)
    assert len(records) == 1
    assert records[0]["job_id"] == "job-2"
    assert records[0]["status"] == "failed"


def test_archive_completed_and_failed(tmp_path, jobs):
    path = archive_jobs(
        jobs,
        archive_dir=str(tmp_path),
        statuses=[RenderStatus.COMPLETED, RenderStatus.FAILED],
    )
    records = load_archive(path)
    assert len(records) == 2


def test_archive_record_fields(tmp_path, jobs):
    path = archive_jobs(jobs, archive_dir=str(tmp_path))
    records = load_archive(path)
    completed = next(r for r in records if r["job_id"] == "job-1")
    assert completed["server"] == "render-01"
    assert completed["frame_range"] == list(range(1, 11))
    assert completed["error_message"] is None
    assert completed["started_at"] is not None
    assert completed["completed_at"] is not None


def test_archive_error_message_preserved(tmp_path, jobs):
    path = archive_jobs(jobs, archive_dir=str(tmp_path))
    records = load_archive(path)
    failed = next(r for r in records if r["job_id"] == "job-2")
    assert failed["error_message"] == "Out of memory"


def test_archive_metadata_present(tmp_path, jobs):
    path = archive_jobs(jobs, archive_dir=str(tmp_path))
    with open(path, "r") as fh:
        data = json.load(fh)
    assert "archived_at" in data
    assert "jobs" in data


def test_archive_empty_list(tmp_path):
    path = archive_jobs([], archive_dir=str(tmp_path), label="empty")
    records = load_archive(path)
    assert records == []


def test_archive_creates_directory(tmp_path, jobs):
    subdir = str(tmp_path / "deep" / "nested")
    path = archive_jobs(jobs, archive_dir=subdir)
    assert os.path.isfile(path)
