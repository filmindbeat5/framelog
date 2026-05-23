"""Checkpoint tracking for long-running render jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Checkpoint:
    """A single progress checkpoint for a render job."""

    label: str
    frame: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "frame": self.frame,
            "timestamp": self.timestamp.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        return cls(
            label=data["label"],
            frame=data["frame"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            note=data.get("note", ""),
        )


class JobCheckpointManager:
    """Manages per-job checkpoints."""

    def __init__(self) -> None:
        self._checkpoints: Dict[str, List[Checkpoint]] = {}

    def add_checkpoint(self, job_id: str, label: str, frame: int, note: str = "") -> Checkpoint:
        """Record a new checkpoint for *job_id*."""
        if not label:
            raise ValueError("Checkpoint label must not be empty.")
        cp = Checkpoint(label=label, frame=frame, note=note)
        self._checkpoints.setdefault(job_id, []).append(cp)
        return cp

    def get_checkpoints(self, job_id: str) -> List[Checkpoint]:
        """Return all checkpoints for *job_id* in insertion order."""
        return list(self._checkpoints.get(job_id, []))

    def latest_checkpoint(self, job_id: str) -> Optional[Checkpoint]:
        """Return the most recent checkpoint or *None* if none exist."""
        cps = self._checkpoints.get(job_id, [])
        return cps[-1] if cps else None

    def clear_checkpoints(self, job_id: str) -> int:
        """Remove all checkpoints for *job_id*. Returns number removed."""
        removed = self._checkpoints.pop(job_id, [])
        return len(removed)

    def all_job_ids(self) -> List[str]:
        """Return job IDs that have at least one checkpoint."""
        return [jid for jid, cps in self._checkpoints.items() if cps]
