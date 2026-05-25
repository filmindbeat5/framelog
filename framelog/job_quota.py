"""Job quota management: enforce per-server and global render job limits."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from framelog.job_status import RenderJob, RenderStatus


@dataclass
class QuotaPolicy:
    global_max: int = 100
    per_server_max: int = 20


@dataclass
class QuotaViolation:
    job_id: str
    server: Optional[str]
    reason: str

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "server": self.server,
            "reason": self.reason,
        }


class JobQuotaManager:
    """Tracks active (running) job counts and enforces quota limits."""

    def __init__(self, policy: Optional[QuotaPolicy] = None) -> None:
        self.policy = policy or QuotaPolicy()
        # server -> count of running jobs
        self._server_counts: Dict[str, int] = {}
        self._global_count: int = 0

    def _running_jobs(self, jobs: list[RenderJob]) -> list[RenderJob]:
        return [j for j in jobs if j.status == RenderStatus.RUNNING]

    def rebuild(self, jobs: list[RenderJob]) -> None:
        """Rebuild counters from a full job list."""
        self._global_count = 0
        self._server_counts = {}
        for job in self._running_jobs(jobs):
            self._global_count += 1
            if job.server:
                self._server_counts[job.server] = (
                    self._server_counts.get(job.server, 0) + 1
                )

    def check(self, job: RenderJob) -> Optional[QuotaViolation]:
        """Return a QuotaViolation if dispatching *job* would exceed limits."""
        if self._global_count >= self.policy.global_max:
            return QuotaViolation(
                job_id=job.job_id,
                server=job.server,
                reason=f"Global limit of {self.policy.global_max} running jobs reached",
            )
        if job.server:
            server_count = self._server_counts.get(job.server, 0)
            if server_count >= self.policy.per_server_max:
                return QuotaViolation(
                    job_id=job.job_id,
                    server=job.server,
                    reason=(
                        f"Server '{job.server}' limit of "
                        f"{self.policy.per_server_max} running jobs reached"
                    ),
                )
        return None

    def record_start(self, job: RenderJob) -> None:
        """Increment counters when a job starts running."""
        self._global_count += 1
        if job.server:
            self._server_counts[job.server] = (
                self._server_counts.get(job.server, 0) + 1
            )

    def record_finish(self, job: RenderJob) -> None:
        """Decrement counters when a job finishes (completed or failed)."""
        self._global_count = max(0, self._global_count - 1)
        if job.server and job.server in self._server_counts:
            self._server_counts[job.server] = max(
                0, self._server_counts[job.server] - 1
            )

    def server_usage(self) -> Dict[str, int]:
        return dict(self._server_counts)

    def global_usage(self) -> int:
        return self._global_count
