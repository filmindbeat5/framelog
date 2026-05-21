"""Job status definitions and tracking model for render jobs."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RenderStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RenderJob:
    job_id: str
    server_id: str
    asset_path: str
    status: RenderStatus = RenderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    frame_count: int = 0
    frames_completed: int = 0

    def start(self) -> None:
        """Mark the job as running."""
        self.status = RenderStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark the job as successfully completed."""
        self.status = RenderStatus.COMPLETED
        self.finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """Mark the job as failed with an error message."""
        self.status = RenderStatus.FAILED
        self.error_message = error_message
        self.finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Mark the job as cancelled."""
        self.status = RenderStatus.CANCELLED
        self.finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def progress(self) -> float:
        """Return completion progress as a percentage (0.0 - 100.0)."""
        if self.frame_count == 0:
            return 0.0
        return round((self.frames_completed / self.frame_count) * 100, 2)

    def to_dict(self) -> dict:
        """Serialize the job to a plain dictionary."""
        return {
            "job_id": self.job_id,
            "server_id": self.server_id,
            "asset_path": self.asset_path,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "error_message": self.error_message,
            "frame_count": self.frame_count,
            "frames_completed": self.frames_completed,
            "progress": self.progress,
        }
