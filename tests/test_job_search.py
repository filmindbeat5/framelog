"""Tests for framelog.job_search."""

import pytest

from framelog.job_status import RenderJob, RenderStatus, start, complete, fail
from framelog.job_search import SearchQuery, search_jobs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def jobs():
    j1 = RenderJob("job-001", "server-a", 1, 50)
    start(j1)
    complete(j1)

    j2 = RenderJob("job-002", "server-b", 51, 100)
    start(j2)
    fail(j2, "out of memory")

    j3 = RenderJob("job-003", "server-a", 101, 150)
    # pending

    return [j1, j2, j3]


# ---------------------------------------------------------------------------
# Tests — text search
# ---------------------------------------------------------------------------

def test_text_matches_job_id(jobs):
    results = search_jobs(jobs, SearchQuery(text="job-001"))
    assert len(results) == 1
    assert results[0].job_id == "job-001"


def test_text_matches_server(jobs):
    results = search_jobs(jobs, SearchQuery(text="server-a"))
    assert len(results) == 2


def test_text_matches_error_message(jobs):
    results = search_jobs(jobs, SearchQuery(text="memory"))
    assert len(results) == 1
    assert results[0].job_id == "job-002"


def test_text_no_match_returns_empty(jobs):
    results = search_jobs(jobs, SearchQuery(text="nonexistent"))
    assert results == []


# ---------------------------------------------------------------------------
# Tests — status filter
# ---------------------------------------------------------------------------

def test_filter_by_completed_status(jobs):
    results = search_jobs(jobs, SearchQuery(status=RenderStatus.COMPLETED))
    assert len(results) == 1
    assert results[0].job_id == "job-001"


def test_filter_by_pending_status(jobs):
    results = search_jobs(jobs, SearchQuery(status=RenderStatus.PENDING))
    assert len(results) == 1
    assert results[0].job_id == "job-003"


# ---------------------------------------------------------------------------
# Tests — server filter
# ---------------------------------------------------------------------------

def test_filter_by_server(jobs):
    results = search_jobs(jobs, SearchQuery(server="server-b"))
    assert len(results) == 1
    assert results[0].job_id == "job-002"


# ---------------------------------------------------------------------------
# Tests — frame range filter
# ---------------------------------------------------------------------------

def test_frame_min_excludes_earlier_jobs(jobs):
    results = search_jobs(jobs, SearchQuery(frame_min=51))
    assert all(j.frame_end >= 51 for j in results)
    assert len(results) == 2


def test_frame_max_excludes_later_jobs(jobs):
    results = search_jobs(jobs, SearchQuery(frame_max=100))
    assert all(j.frame_start <= 100 for j in results)
    assert len(results) == 2


def test_frame_range_exact_match(jobs):
    results = search_jobs(jobs, SearchQuery(frame_min=51, frame_max=100))
    assert len(results) == 1
    assert results[0].job_id == "job-002"


# ---------------------------------------------------------------------------
# Tests — tag filter
# ---------------------------------------------------------------------------

def test_tags_without_manager_returns_empty(jobs):
    results = search_jobs(jobs, SearchQuery(tags=["urgent"]), tag_manager=None)
    assert results == []


def test_tags_with_manager_filters_correctly(jobs):
    from framelog.job_tags import JobTagManager
    mgr = JobTagManager()
    mgr.add_tag("job-001", "urgent")
    mgr.add_tag("job-002", "urgent")

    results = search_jobs(jobs, SearchQuery(tags=["urgent"]), tag_manager=mgr)
    assert {j.job_id for j in results} == {"job-001", "job-002"}


# ---------------------------------------------------------------------------
# Tests — combined filters
# ---------------------------------------------------------------------------

def test_combined_server_and_status(jobs):
    results = search_jobs(
        jobs,
        SearchQuery(server="server-a", status=RenderStatus.COMPLETED),
    )
    assert len(results) == 1
    assert results[0].job_id == "job-001"


def test_empty_query_returns_all(jobs):
    results = search_jobs(jobs, SearchQuery())
    assert len(results) == len(jobs)
