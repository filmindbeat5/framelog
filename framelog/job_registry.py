"""Registry for tracking and querying multiple render jobs across distributed media servers."""

from typing import Dict, List, Optional
from datetime import datetime

from framelog.job_status import RenderJob, RenderStatus


class JobRegistry:
    """Central registry for managing and querying render jobs."""

    def __init__(self):
        self._jobs: Dict[str, RenderJob] = {}

    def register(self, job: RenderJob) -> None:
        """Register a render job in the registry."""
        if job.job_id in self._jobs:
            raise ValueError(f"Job '{job.job_id}' is already registered.")
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> Optional[RenderJob]:
        """Retrieve a job by its ID. Returns None if not found."""
        return self._jobs.get(job_id)

    def all_jobs(self) -> List[RenderJob]:
        """Return a list of all registered jobs."""
        return list(self._jobs.values())

    def jobs_by_status(self, status: RenderStatus) -> List[RenderJob]:
        """Return all jobs matching a given status."""
        return [job for job in self._jobs.values() if job.status == status]

    def jobs_by_server(self, server_id: str) -> List[RenderJob]:
        """Return all jobs assigned to a specific server."""
        return [job for job in self._jobs.values() if job.server_id == server_id]

    def summary(self) -> Dict[str, int]:
        """Return a count of jobs grouped by status."""
        counts: Dict[str, int] = {status.value: 0 for status in RenderStatus}
        for job in self._jobs.values():
            counts[job.status.value] += 1
        return counts

    def remove(self, job_id: str) -> None:
        """Remove a job from the registry by its ID."""
        if job_id not in self._jobs:
            raise KeyError(f"Job '{job_id}' not found in registry.")
        del self._jobs[job_id]

    def clear(self) -> None:
        """Remove all jobs from the registry."""
        self._jobs.clear()

    def __len__(self) -> int:
        return len(self._jobs)

    def __contains__(self, job_id: str) -> bool:
        return job_id in self._jobs
