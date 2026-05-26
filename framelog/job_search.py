"""Full-text and field-based search across render jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from framelog.job_status import RenderJob, RenderStatus


@dataclass
class SearchQuery:
    """Parameters for a job search."""

    text: Optional[str] = None  # matched against job_id, server, error_message
    status: Optional[RenderStatus] = None
    server: Optional[str] = None
    tags: List[str] = field(default_factory=list)  # all tags must be present
    frame_min: Optional[int] = None
    frame_max: Optional[int] = None


def _matches_text(job: RenderJob, text: str) -> bool:
    needle = text.lower()
    haystack = " ".join(
        filter(None, [job.job_id, job.server, job.error_message or ""])
    ).lower()
    return needle in haystack


def _matches_frame_range(job: RenderJob, frame_min: Optional[int], frame_max: Optional[int]) -> bool:
    if frame_min is not None and job.frame_end < frame_min:
        return False
    if frame_max is not None and job.frame_start > frame_max:
        return False
    return True


def search_jobs(
    jobs: List[RenderJob],
    query: SearchQuery,
    tag_manager=None,
) -> List[RenderJob]:
    """Return jobs that satisfy all non-None fields in *query*.

    *tag_manager* should be a :class:`~framelog.job_tags.JobTagManager` instance
    when ``query.tags`` is non-empty; otherwise tag filtering is skipped.
    """
    results: List[RenderJob] = []

    for job in jobs:
        if query.text and not _matches_text(job, query.text):
            continue
        if query.status is not None and job.status != query.status:
            continue
        if query.server and job.server != query.server:
            continue
        if not _matches_frame_range(job, query.frame_min, query.frame_max):
            continue
        if query.tags:
            if tag_manager is None:
                continue
            job_tags = tag_manager.get_tags(job.job_id)
            if not all(t in job_tags for t in query.tags):
                continue
        results.append(job)

    return results
