"""Retry logic for failed render jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from framelog.job_status import RenderJob, RenderStatus


@dataclass
class RetryPolicy:
    """Defines how many times a job may be retried and under what conditions."""

    max_attempts: int = 3
    retry_on_statuses: tuple = (RenderStatus.FAILED,)


@dataclass
class RetryRecord:
    """Tracks retry attempts for a single job."""

    job_id: str
    attempts: int = 0
    last_error: Optional[str] = None


class JobRetryManager:
    """Manages retry state and eligibility for render jobs."""

    def __init__(self, policy: Optional[RetryPolicy] = None) -> None:
        self.policy = policy or RetryPolicy()
        self._records: Dict[str, RetryRecord] = {}

    def _get_record(self, job: RenderJob) -> RetryRecord:
        if job.job_id not in self._records:
            self._records[job.job_id] = RetryRecord(job_id=job.job_id)
        return self._records[job.job_id]

    def can_retry(self, job: RenderJob) -> bool:
        """Return True if the job is eligible for another retry attempt."""
        if job.status not in self.policy.retry_on_statuses:
            return False
        record = self._get_record(job)
        return record.attempts < self.policy.max_attempts

    def retry(self, job: RenderJob) -> bool:
        """Reset a failed job to PENDING and increment attempt counter.

        Returns True if the retry was applied, False if not eligible.
        """
        if not self.can_retry(job):
            return False
        record = self._get_record(job)
        record.last_error = job.error_message
        record.attempts += 1
        job.status = RenderStatus.PENDING
        job.error_message = None
        return True

    def attempts(self, job: RenderJob) -> int:
        """Return the number of retry attempts made for a job."""
        return self._get_record(job).attempts

    def last_error(self, job: RenderJob) -> Optional[str]:
        """Return the error message from the most recent failure."""
        return self._get_record(job).last_error

    def exhausted(self, job: RenderJob) -> bool:
        """Return True if the job has used all allowed retry attempts."""
        return (
            job.status in self.policy.retry_on_statuses
            and self._get_record(job).attempts >= self.policy.max_attempts
        )
