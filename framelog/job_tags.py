"""Tag management for render jobs — attach, remove, and query tags on RenderJob instances."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Set

from framelog.job_status import RenderJob


class JobTagManager:
    """Maintains a many-to-many mapping between jobs and string tags."""

    def __init__(self) -> None:
        # job_id -> set of tags
        self._tags: Dict[str, Set[str]] = defaultdict(set)

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_tag(self, job: RenderJob, tag: str) -> None:
        """Attach *tag* to *job*."""
        self._tags[job.job_id].add(tag.strip().lower())

    def add_tags(self, job: RenderJob, tags: Iterable[str]) -> None:
        """Attach multiple tags at once."""
        for tag in tags:
            self.add_tag(job, tag)

    def remove_tag(self, job: RenderJob, tag: str) -> None:
        """Remove *tag* from *job* (no-op if absent)."""
        self._tags[job.job_id].discard(tag.strip().lower())

    def clear_tags(self, job: RenderJob) -> None:
        """Remove all tags from *job*."""
        self._tags.pop(job.job_id, None)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_tags(self, job: RenderJob) -> Set[str]:
        """Return the set of tags currently assigned to *job*."""
        return set(self._tags.get(job.job_id, set()))

    def has_tag(self, job: RenderJob, tag: str) -> bool:
        """Return True if *job* carries *tag*."""
        return tag.strip().lower() in self._tags.get(job.job_id, set())

    def filter_by_tag(self, jobs: Iterable[RenderJob], tag: str) -> List[RenderJob]:
        """Return jobs from *jobs* that carry *tag*."""
        normalised = tag.strip().lower()
        return [j for j in jobs if normalised in self._tags.get(j.job_id, set())]

    def filter_by_tags_all(self, jobs: Iterable[RenderJob], tags: Iterable[str]) -> List[RenderJob]:
        """Return jobs that carry *all* of the given tags."""
        required = {t.strip().lower() for t in tags}
        return [j for j in jobs if required.issubset(self._tags.get(j.job_id, set()))]

    def filter_by_tags_any(self, jobs: Iterable[RenderJob], tags: Iterable[str]) -> List[RenderJob]:
        """Return jobs that carry *at least one* of the given tags."""
        wanted = {t.strip().lower() for t in tags}
        return [j for j in jobs if wanted & self._tags.get(j.job_id, set())]

    def all_tags(self) -> Set[str]:
        """Return the union of every tag currently in use."""
        result: Set[str] = set()
        for tags in self._tags.values():
            result |= tags
        return result
