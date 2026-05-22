"""Priority management for render jobs in the scheduling queue."""

from __future__ import annotations

from enum import IntEnum
from typing import Dict, List, Optional

from framelog.job_status import RenderJob


class Priority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class JobPriorityManager:
    """Assigns and tracks priority levels for render jobs."""

    def __init__(self) -> None:
        self._priorities: Dict[str, Priority] = {}

    def set_priority(self, job: RenderJob, priority: Priority) -> None:
        """Assign a priority level to a job."""
        self._priorities[job.job_id] = priority

    def get_priority(self, job: RenderJob) -> Priority:
        """Return the priority for a job, defaulting to NORMAL."""
        return self._priorities.get(job.job_id, Priority.NORMAL)

    def remove_priority(self, job: RenderJob) -> None:
        """Remove any explicit priority assignment for a job."""
        self._priorities.pop(job.job_id, None)

    def sort_jobs(self, jobs: List[RenderJob]) -> List[RenderJob]:
        """Return jobs sorted from highest to lowest priority."""
        return sorted(jobs, key=lambda j: self.get_priority(j), reverse=True)

    def jobs_at_priority(
        self, jobs: List[RenderJob], priority: Priority
    ) -> List[RenderJob]:
        """Filter jobs that match an exact priority level."""
        return [j for j in jobs if self.get_priority(j) == priority]

    def promote(self, job: RenderJob) -> Optional[Priority]:
        """Raise a job's priority by one level. Returns new priority or None if already CRITICAL."""
        current = self.get_priority(job)
        if current == Priority.CRITICAL:
            return None
        new_priority = Priority(current + 1)
        self._priorities[job.job_id] = new_priority
        return new_priority

    def demote(self, job: RenderJob) -> Optional[Priority]:
        """Lower a job's priority by one level. Returns new priority or None if already LOW."""
        current = self.get_priority(job)
        if current == Priority.LOW:
            return None
        new_priority = Priority(current - 1)
        self._priorities[job.job_id] = new_priority
        return new_priority
