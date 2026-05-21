"""Tests for RenderJob status tracking and transitions."""

import pytest
from datetime import datetime

from framelog.job_status import RenderJob, RenderStatus


@pytest.fixture
def sample_job() -> RenderJob:
    return RenderJob(
        job_id="job-001",
        server_id="server-us-east-1",
        asset_path="/renders/scene_42.blend",
        frame_count=100,
    )


def test_default_status_is_pending(sample_job):
    assert sample_job.status == RenderStatus.PENDING


def test_start_sets_running_status(sample_job):
    sample_job.start()
    assert sample_job.status == RenderStatus.RUNNING
    assert sample_job.started_at is not None


def test_complete_sets_completed_status(sample_job):
    sample_job.start()
    sample_job.complete()
    assert sample_job.status == RenderStatus.COMPLETED
    assert sample_job.finished_at is not None


def test_fail_sets_failed_status_and_message(sample_job):
    sample_job.start()
    sample_job.fail("Out of memory")
    assert sample_job.status == RenderStatus.FAILED
    assert sample_job.error_message == "Out of memory"
    assert sample_job.finished_at is not None


def test_cancel_sets_cancelled_status(sample_job):
    sample_job.cancel()
    assert sample_job.status == RenderStatus.CANCELLED
    assert sample_job.finished_at is not None


def test_progress_zero_when_no_frames_completed(sample_job):
    assert sample_job.progress == 0.0


def test_progress_calculation(sample_job):
    sample_job.frames_completed = 50
    assert sample_job.progress == 50.0


def test_progress_full_completion(sample_job):
    sample_job.frames_completed = 100
    assert sample_job.progress == 100.0


def test_progress_zero_frame_count():
    job = RenderJob(job_id="j", server_id="s", asset_path="/p", frame_count=0)
    assert job.progress == 0.0


def test_to_dict_contains_expected_keys(sample_job):
    result = sample_job.to_dict()
    expected_keys = {
        "job_id", "server_id", "asset_path", "status",
        "created_at", "updated_at", "started_at", "finished_at",
        "error_message", "frame_count", "frames_completed", "progress",
    }
    assert expected_keys == set(result.keys())


def test_to_dict_status_is_string(sample_job):
    result = sample_job.to_dict()
    assert result["status"] == "pending"


def test_to_dict_started_at_none_before_start(sample_job):
    result = sample_job.to_dict()
    assert result["started_at"] is None


def test_to_dict_started_at_set_after_start(sample_job):
    sample_job.start()
    result = sample_job.to_dict()
    assert result["started_at"] is not None
