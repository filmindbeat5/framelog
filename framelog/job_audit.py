"""Audit log for tracking state changes and actions on render jobs."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict


@dataclass
class AuditEntry:
    job_id: str
    action: str
    actor: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detail: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "action": self.action,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            job_id=data["job_id"],
            action=data["action"],
            actor=data["actor"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            detail=data.get("detail"),
        )


class JobAuditManager:
    def __init__(self) -> None:
        self._log: List[AuditEntry] = []

    def record(self, job_id: str, action: str, actor: str, detail: Optional[str] = None) -> AuditEntry:
        if not job_id:
            raise ValueError("job_id must not be empty")
        if not action:
            raise ValueError("action must not be empty")
        if not actor:
            raise ValueError("actor must not be empty")
        entry = AuditEntry(job_id=job_id, action=action, actor=actor, detail=detail)
        self._log.append(entry)
        return entry

    def entries_for_job(self, job_id: str) -> List[AuditEntry]:
        return [e for e in self._log if e.job_id == job_id]

    def entries_by_actor(self, actor: str) -> List[AuditEntry]:
        return [e for e in self._log if e.actor == actor]

    def entries_by_action(self, action: str) -> List[AuditEntry]:
        return [e for e in self._log if e.action == action]

    def all_entries(self) -> List[AuditEntry]:
        return list(self._log)

    def to_dict_list(self) -> List[dict]:
        return [e.to_dict() for e in self._log]

    def load_from_dict_list(self, data: List[dict]) -> None:
        self._log = [AuditEntry.from_dict(d) for d in data]

    def grouped_by_job(self) -> Dict[str, List[AuditEntry]]:
        result: Dict[str, List[AuditEntry]] = {}
        for entry in self._log:
            result.setdefault(entry.job_id, []).append(entry)
        return result
