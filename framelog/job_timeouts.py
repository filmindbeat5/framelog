"""Timeout tracking and detection for render jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from framelog.job_status import RenderJob, RenderStatus


@dataclass
class TimeoutPolicy:
    """Defines how long a job may remain in a given status before timing out."""

    max_running_seconds: float = 3600.0   # 1 hour default
    max_pending_seconds: float = 7200.0   # 2 hours default


@dataclass
class TimeoutEvent:
    """Represents a detected timeout for a single job."""

    job_id: str
    status_at_timeout: RenderStatus
    elapsed_seconds: float
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status_at_timeout": self.status_at_timeout.value,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "detected_at": self.detected_at.isoformat(),
        }


class JobTimeoutManager:
    """Scans jobs and emits TimeoutEvents for jobs that have exceeded policy limits."""

    def __init__(self, policy: Optional[TimeoutPolicy] = None) -> None:
        self._policy = policy or TimeoutPolicy()
        self._suppressed: set = set()

    @property
    def policy(self) -> TimeoutPolicy:
        return self._policy

    def suppress(self, job_id: str) -> None:
        """Prevent a job from generating further timeout events."""
        self._suppressed.add(job_id)

    def is_suppressed(self, job_id: str) -> bool:
        return job_id in self._suppressed

    def check_job(self, job: RenderJob, now: Optional[datetime] = None) -> Optional[TimeoutEvent]:
        """Return a TimeoutEvent if the job has exceeded its allowed duration, else None."""
        if job.job_id in self._suppressed:
            return None

        now = now or datetime.utcnow()
        reference: Optional[datetime] = None
        limit: Optional[float] = None

        if job.status == RenderStatus.RUNNING and job.started_at:
            reference = job.started_at
            limit = self._policy.max_running_seconds
        elif job.status == RenderStatus.PENDING and job.created_at:
            reference = job.created_at
            limit = self._policy.max_pending_seconds

        if reference is None or limit is None:
            return None

        elapsed = (now - reference).total_seconds()
        if elapsed > limit:
            return TimeoutEvent(
                job_id=job.job_id,
                status_at_timeout=job.status,
                elapsed_seconds=elapsed,
                detected_at=now,
            )
        return None

    def scan(self, jobs: List[RenderJob], now: Optional[datetime] = None) -> List[TimeoutEvent]:
        """Scan a list of jobs and return all detected timeout events."""
        now = now or datetime.utcnow()
        events: List[TimeoutEvent] = []
        for job in jobs:
            event = self.check_job(job, now=now)
            if event:
                events.append(event)
        return events
