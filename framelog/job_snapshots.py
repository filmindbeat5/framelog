"""Periodic state snapshots for render jobs, enabling point-in-time restore and diff."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from framelog.job_status import RenderJob, RenderStatus


@dataclass
class JobSnapshot:
    job_id: str
    status: str
    server: Optional[str]
    frame_start: int
    frame_end: int
    error_message: Optional[str]
    captured_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "server": self.server,
            "frame_start": self.frame_start,
            "frame_end": self.frame_end,
            "error_message": self.error_message,
            "captured_at": self.captured_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JobSnapshot":
        return cls(
            job_id=data["job_id"],
            status=data["status"],
            server=data.get("server"),
            frame_start=data["frame_start"],
            frame_end=data["frame_end"],
            error_message=data.get("error_message"),
            captured_at=data["captured_at"],
        )

    @classmethod
    def capture(cls, job: RenderJob) -> "JobSnapshot":
        return cls(
            job_id=job.job_id,
            status=job.status.value,
            server=job.server,
            frame_start=job.frame_start,
            frame_end=job.frame_end,
            error_message=job.error_message,
        )


class JobSnapshotManager:
    """Stores and retrieves ordered snapshots per job."""

    def __init__(self) -> None:
        self._snapshots: Dict[str, List[JobSnapshot]] = {}

    def capture(self, job: RenderJob) -> JobSnapshot:
        snap = JobSnapshot.capture(job)
        self._snapshots.setdefault(job.job_id, []).append(snap)
        return snap

    def history(self, job_id: str) -> List[JobSnapshot]:
        return list(self._snapshots.get(job_id, []))

    def latest(self, job_id: str) -> Optional[JobSnapshot]:
        snaps = self._snapshots.get(job_id)
        return snaps[-1] if snaps else None

    def diff(self, job_id: str) -> List[dict]:
        """Return list of field-level diffs between consecutive snapshots."""
        snaps = self.history(job_id)
        if len(snaps) < 2:
            return []
        results = []
        for prev, curr in zip(snaps, snaps[1:]):
            changes = {
                k: {"from": prev.to_dict()[k], "to": curr.to_dict()[k]}
                for k in prev.to_dict()
                if k != "captured_at" and prev.to_dict()[k] != curr.to_dict()[k]
            }
            if changes:
                results.append({"captured_at": curr.captured_at, "changes": changes})
        return results

    def clear(self, job_id: str) -> None:
        self._snapshots.pop(job_id, None)
