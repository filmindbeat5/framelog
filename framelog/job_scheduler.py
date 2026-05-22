"""Priority-based job scheduling for render queues."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import List, Optional

from framelog.job_status import RenderJob, RenderStatus


@dataclass(order=True)
class ScheduledJob:
    priority: int
    job: RenderJob = field(compare=False)


class JobScheduler:
    """Manages a priority queue of render jobs awaiting dispatch."""

    def __init__(self) -> None:
        self._heap: List[ScheduledJob] = []
        self._job_ids: set = set()

    def enqueue(self, job: RenderJob, priority: int = 10) -> None:
        """Add a job to the scheduler. Lower priority value = higher urgency."""
        if job.job_id in self._job_ids:
            raise ValueError(f"Job '{job.job_id}' is already scheduled.")
        if job.status != RenderStatus.PENDING:
            raise ValueError(
                f"Only PENDING jobs can be scheduled; got {job.status.value}."
            )
        entry = ScheduledJob(priority=priority, job=job)
        heapq.heappush(self._heap, entry)
        self._job_ids.add(job.job_id)

    def dequeue(self) -> Optional[RenderJob]:
        """Remove and return the highest-priority job, or None if empty."""
        while self._heap:
            entry = heapq.heappop(self._heap)
            self._job_ids.discard(entry.job.job_id)
            return entry.job
        return None

    def peek(self) -> Optional[RenderJob]:
        """Return the next job without removing it."""
        if self._heap:
            return self._heap[0].job
        return None

    def remove(self, job_id: str) -> bool:
        """Remove a job by ID. Returns True if found and removed."""
        for i, entry in enumerate(self._heap):
            if entry.job.job_id == job_id:
                self._heap.pop(i)
                heapq.heapify(self._heap)
                self._job_ids.discard(job_id)
                return True
        return False

    def pending_count(self) -> int:
        """Return number of jobs currently in the queue."""
        return len(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def all_scheduled(self) -> List[RenderJob]:
        """Return all scheduled jobs sorted by priority (non-destructive)."""
        return [e.job for e in sorted(self._heap)]
