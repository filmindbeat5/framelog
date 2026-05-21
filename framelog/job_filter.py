"""Filtering utilities for querying RenderJob collections by status, server, or time range."""

from datetime import datetime
from typing import List, Optional

from framelog.job_status import RenderJob, RenderStatus


def filter_by_status(jobs: List[RenderJob], status: RenderStatus) -> List[RenderJob]:
    """Return jobs matching the given RenderStatus."""
    return [job for job in jobs if job.status == status]


def filter_by_server(jobs: List[RenderJob], server_id: str) -> List[RenderJob]:
    """Return jobs assigned to the specified server."""
    return [job for job in jobs if job.server_id == server_id]


def filter_by_time_range(
    jobs: List[RenderJob],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[RenderJob]:
    """Return jobs whose created_at timestamp falls within [start, end].

    Either bound may be omitted to apply an open-ended range.
    """
    result = []
    for job in jobs:
        created = job.created_at
        if start is not None and created < start:
            continue
        if end is not None and created > end:
            continue
        result.append(job)
    return result


def filter_failed_with_message(jobs: List[RenderJob], keyword: str) -> List[RenderJob]:
    """Return failed jobs whose error message contains the given keyword (case-insensitive)."""
    keyword_lower = keyword.lower()
    return [
        job
        for job in jobs
        if job.status == RenderStatus.FAILED
        and job.error_message is not None
        and keyword_lower in job.error_message.lower()
    ]


def group_by_status(jobs: List[RenderJob]) -> dict:
    """Return a dict mapping each RenderStatus to the list of jobs in that state."""
    groups: dict = {status: [] for status in RenderStatus}
    for job in jobs:
        groups[job.status].append(job)
    return groups
