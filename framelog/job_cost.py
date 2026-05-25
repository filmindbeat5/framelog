"""Tracks estimated compute cost per render job based on duration and server."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from framelog.job_status import RenderJob, RenderStatus


@dataclass
class CostRate:
    """Cost rate configuration for a server (cost per second)."""
    server_id: str
    cost_per_second: float  # e.g. 0.05 USD/sec


@dataclass
class JobCostEntry:
    job_id: str
    server_id: Optional[str]
    duration_seconds: Optional[float]
    cost_per_second: float
    estimated_cost: float

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "server_id": self.server_id,
            "duration_seconds": self.duration_seconds,
            "cost_per_second": self.cost_per_second,
            "estimated_cost": round(self.estimated_cost, 6),
        }


class JobCostManager:
    """Calculates and stores cost estimates for render jobs."""

    DEFAULT_RATE = 0.01  # fallback cost per second

    def __init__(self) -> None:
        self._rates: Dict[str, float] = {}
        self._entries: Dict[str, JobCostEntry] = {}

    def set_rate(self, server_id: str, cost_per_second: float) -> None:
        """Register a cost rate for a specific server."""
        if cost_per_second < 0:
            raise ValueError("cost_per_second must be non-negative")
        self._rates[server_id] = cost_per_second

    def get_rate(self, server_id: Optional[str]) -> float:
        if server_id and server_id in self._rates:
            return self._rates[server_id]
        return self.DEFAULT_RATE

    def calculate(self, job: RenderJob) -> Optional[JobCostEntry]:
        """Calculate cost for a completed or failed job. Returns None if duration unavailable."""
        if job.started_at is None or job.finished_at is None:
            return None
        duration = (job.finished_at - job.started_at).total_seconds()
        if duration < 0:
            duration = 0.0
        rate = self.get_rate(job.server_id)
        cost = duration * rate
        entry = JobCostEntry(
            job_id=job.job_id,
            server_id=job.server_id,
            duration_seconds=duration,
            cost_per_second=rate,
            estimated_cost=cost,
        )
        self._entries[job.job_id] = entry
        return entry

    def get_entry(self, job_id: str) -> Optional[JobCostEntry]:
        return self._entries.get(job_id)

    def total_cost(self) -> float:
        return sum(e.estimated_cost for e in self._entries.values())

    def cost_by_server(self) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for entry in self._entries.values():
            key = entry.server_id or "unknown"
            result[key] = round(result.get(key, 0.0) + entry.estimated_cost, 6)
        return result
