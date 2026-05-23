"""Track per-job render progress as a percentage (0–100)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from framelog.job_status import RenderJob, RenderStatus


@dataclass
class ProgressSnapshot:
    job_id: str
    percent: float          # 0.0 – 100.0
    frames_done: int
    frames_total: int
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "percent": self.percent,
            "frames_done": self.frames_done,
            "frames_total": self.frames_total,
            "message": self.message,
        }


class JobProgressManager:
    """Records and queries render progress for tracked jobs."""

    def __init__(self) -> None:
        self._progress: Dict[str, ProgressSnapshot] = {}

    # ------------------------------------------------------------------
    def update(self, job: RenderJob, frames_done: int, message: str = "") -> ProgressSnapshot:
        """Update progress for *job*.  Raises ValueError for bad frame counts."""
        frames_total = job.frame_end - job.frame_start + 1
        if frames_total <= 0:
            raise ValueError(f"Job {job.job_id!r} has an invalid frame range.")
        if frames_done < 0 or frames_done > frames_total:
            raise ValueError(
                f"frames_done={frames_done} is out of range [0, {frames_total}]."
            )
        percent = round((frames_done / frames_total) * 100.0, 2)
        snap = ProgressSnapshot(
            job_id=job.job_id,
            percent=percent,
            frames_done=frames_done,
            frames_total=frames_total,
            message=message,
        )
        self._progress[job.job_id] = snap
        return snap

    def get(self, job_id: str) -> Optional[ProgressSnapshot]:
        """Return the latest snapshot for *job_id*, or None if not tracked."""
        return self._progress.get(job_id)

    def all_snapshots(self) -> list[ProgressSnapshot]:
        """Return all snapshots sorted by job_id."""
        return sorted(self._progress.values(), key=lambda s: s.job_id)

    def clear(self, job_id: str) -> None:
        """Remove tracking data for *job_id* (no-op if unknown)."""
        self._progress.pop(job_id, None)

    def completed_jobs(self) -> list[ProgressSnapshot]:
        """Return snapshots where percent == 100.0."""
        return [s for s in self._progress.values() if s.percent >= 100.0]
