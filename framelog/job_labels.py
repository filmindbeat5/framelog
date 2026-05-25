"""Manage human-readable labels (aliases) for render jobs."""

from __future__ import annotations

from typing import Dict, List, Optional


class LabelConflictError(Exception):
    """Raised when a label is already assigned to a different job."""


class JobLabelManager:
    """Assigns and resolves short, human-readable labels for jobs."""

    def __init__(self) -> None:
        self._label_to_id: Dict[str, str] = {}
        self._id_to_labels: Dict[str, List[str]] = {}

    def assign(self, job_id: str, label: str) -> None:
        """Assign *label* to *job_id*.

        Raises:
            ValueError: if job_id or label is empty.
            LabelConflictError: if label is already assigned to a different job.
        """
        if not job_id:
            raise ValueError("job_id must not be empty")
        if not label:
            raise ValueError("label must not be empty")

        existing = self._label_to_id.get(label)
        if existing is not None and existing != job_id:
            raise LabelConflictError(
                f"Label '{label}' is already assigned to job '{existing}'"
            )

        self._label_to_id[label] = job_id
        self._id_to_labels.setdefault(job_id, []).append(label)
        # Deduplicate while preserving order
        seen: set = set()
        unique: List[str] = []
        for lbl in self._id_to_labels[job_id]:
            if lbl not in seen:
                seen.add(lbl)
                unique.append(lbl)
        self._id_to_labels[job_id] = unique

    def unassign(self, label: str) -> None:
        """Remove a label mapping.  No-op if label does not exist."""
        job_id = self._label_to_id.pop(label, None)
        if job_id and job_id in self._id_to_labels:
            self._id_to_labels[job_id] = [
                lbl for lbl in self._id_to_labels[job_id] if lbl != label
            ]

    def resolve(self, label: str) -> Optional[str]:
        """Return the job_id for *label*, or None if not found."""
        return self._label_to_id.get(label)

    def labels_for(self, job_id: str) -> List[str]:
        """Return all labels assigned to *job_id*."""
        return list(self._id_to_labels.get(job_id, []))

    def all_labels(self) -> Dict[str, str]:
        """Return a copy of the full label → job_id mapping."""
        return dict(self._label_to_id)
