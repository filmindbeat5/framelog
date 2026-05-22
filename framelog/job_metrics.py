"""Metrics aggregation for render job performance analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Optional

from framelog.job_status import RenderJob, RenderStatus


@dataclass
class ServerMetrics:
    server: str
    total: int = 0
    completed: int = 0
    failed: int = 0
    durations: List[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.completed / self.total

    @property
    def avg_duration_seconds(self) -> Optional[float]:
        if not self.durations:
            return None
        return sum(self.durations) / len(self.durations)


@dataclass
class JobMetrics:
    total_jobs: int = 0
    by_status: Dict[str, int] = field(default_factory=dict)
    by_server: Dict[str, ServerMetrics] = field(default_factory=dict)
    overall_avg_duration_seconds: Optional[float] = None


def _job_duration(job: RenderJob) -> Optional[float]:
    """Return duration in seconds if both timestamps are present."""
    if job.started_at is None or job.completed_at is None:
        return None
    delta: timedelta = job.completed_at - job.started_at
    return delta.total_seconds()


def compute_metrics(jobs: List[RenderJob]) -> JobMetrics:
    """Compute aggregate metrics from a list of RenderJob instances."""
    metrics = JobMetrics(total_jobs=len(jobs))
    all_durations: List[float] = []

    for job in jobs:
        status_key = job.status.value
        metrics.by_status[status_key] = metrics.by_status.get(status_key, 0) + 1

        server = job.server or "unknown"
        if server not in metrics.by_server:
            metrics.by_server[server] = ServerMetrics(server=server)
        sm = metrics.by_server[server]
        sm.total += 1
        if job.status == RenderStatus.COMPLETED:
            sm.completed += 1
        elif job.status == RenderStatus.FAILED:
            sm.failed += 1

        duration = _job_duration(job)
        if duration is not None:
            sm.durations.append(duration)
            all_durations.append(duration)

    if all_durations:
        metrics.overall_avg_duration_seconds = sum(all_durations) / len(all_durations)

    return metrics
