"""Attach and retrieve timestamped notes on render jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class JobNote:
    """A single timestamped note attached to a job."""

    author: str
    text: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "author": self.author,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JobNote":
        return cls(
            author=data["author"],
            text=data["text"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class JobNotesManager:
    """Manages notes keyed by job ID."""

    def __init__(self) -> None:
        self._notes: Dict[str, List[JobNote]] = {}

    def add_note(self, job_id: str, author: str, text: str) -> JobNote:
        """Add a note to *job_id* and return the created note."""
        if not text.strip():
            raise ValueError("Note text must not be empty.")
        note = JobNote(author=author, text=text)
        self._notes.setdefault(job_id, []).append(note)
        return note

    def get_notes(self, job_id: str) -> List[JobNote]:
        """Return all notes for *job_id* in chronological order."""
        return list(self._notes.get(job_id, []))

    def clear_notes(self, job_id: str) -> int:
        """Remove all notes for *job_id*; return the number removed."""
        removed = self._notes.pop(job_id, [])
        return len(removed)

    def search_notes(self, keyword: str) -> Dict[str, List[JobNote]]:
        """Return notes containing *keyword* (case-insensitive), grouped by job ID."""
        keyword_lower = keyword.lower()
        return {
            job_id: [n for n in notes if keyword_lower in n.text.lower()]
            for job_id, notes in self._notes.items()
            if any(keyword_lower in n.text.lower() for n in notes)
        }

    def all_job_ids_with_notes(self) -> List[str]:
        """Return a sorted list of job IDs that have at least one note."""
        return sorted(self._notes.keys())
