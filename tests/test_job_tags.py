"""Tests for framelog.job_tags.JobTagManager."""

import pytest

from framelog.job_status import RenderJob
from framelog.job_tags import JobTagManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def manager() -> JobTagManager:
    return JobTagManager()


@pytest.fixture()
def job_a() -> RenderJob:
    return RenderJob(job_id="job-a", scene="scene_a.blend", server="render-01", frame_range=(1, 10))


@pytest.fixture()
def job_b() -> RenderJob:
    return RenderJob(job_id="job-b", scene="scene_b.blend", server="render-02", frame_range=(1, 5))


# ---------------------------------------------------------------------------
# Basic add / get
# ---------------------------------------------------------------------------

def test_get_tags_empty(manager, job_a):
    assert manager.get_tags(job_a) == set()


def test_add_single_tag(manager, job_a):
    manager.add_tag(job_a, "urgent")
    assert "urgent" in manager.get_tags(job_a)


def test_add_tags_bulk(manager, job_a):
    manager.add_tags(job_a, ["urgent", "vfx", "client-x"])
    assert manager.get_tags(job_a) == {"urgent", "vfx", "client-x"}


def test_tag_is_normalised_to_lowercase(manager, job_a):
    manager.add_tag(job_a, "  Urgent  ")
    assert manager.has_tag(job_a, "urgent")


# ---------------------------------------------------------------------------
# Remove / clear
# ---------------------------------------------------------------------------

def test_remove_tag(manager, job_a):
    manager.add_tags(job_a, ["urgent", "vfx"])
    manager.remove_tag(job_a, "urgent")
    assert "urgent" not in manager.get_tags(job_a)
    assert "vfx" in manager.get_tags(job_a)


def test_remove_nonexistent_tag_is_noop(manager, job_a):
    manager.add_tag(job_a, "vfx")
    manager.remove_tag(job_a, "missing")
    assert manager.get_tags(job_a) == {"vfx"}


def test_clear_tags(manager, job_a):
    manager.add_tags(job_a, ["urgent", "vfx"])
    manager.clear_tags(job_a)
    assert manager.get_tags(job_a) == set()


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_by_tag(manager, job_a, job_b):
    manager.add_tag(job_a, "urgent")
    manager.add_tag(job_b, "vfx")
    result = manager.filter_by_tag([job_a, job_b], "urgent")
    assert result == [job_a]


def test_filter_by_tags_all(manager, job_a, job_b):
    manager.add_tags(job_a, ["urgent", "vfx"])
    manager.add_tag(job_b, "urgent")
    result = manager.filter_by_tags_all([job_a, job_b], ["urgent", "vfx"])
    assert result == [job_a]


def test_filter_by_tags_any(manager, job_a, job_b):
    manager.add_tag(job_a, "urgent")
    manager.add_tag(job_b, "vfx")
    result = manager.filter_by_tags_any([job_a, job_b], ["urgent", "vfx"])
    assert set(result) == {job_a, job_b}


# ---------------------------------------------------------------------------
# all_tags
# ---------------------------------------------------------------------------

def test_all_tags(manager, job_a, job_b):
    manager.add_tags(job_a, ["urgent", "vfx"])
    manager.add_tag(job_b, "client-x")
    assert manager.all_tags() == {"urgent", "vfx", "client-x"}


def test_all_tags_empty(manager):
    assert manager.all_tags() == set()
