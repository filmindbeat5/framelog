"""Job grouping — assign render jobs to named groups and query membership."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional


class GroupConflictError(Exception):  # noqa: N818
    """Raised when a job is already a member of an exclusive group."""


class JobGroupManager:
    """Manages named groups of render jobs."""

    def __init__(self) -> None:
        # group_name -> set of job_ids
        self._groups: Dict[str, set] = defaultdict(set)
        # job_id -> set of group_names
        self._membership: Dict[str, set] = defaultdict(set)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_to_group(self, job_id: str, group: str) -> None:
        """Add *job_id* to *group*.  Idempotent."""
        if not job_id:
            raise ValueError("job_id must not be empty")
        if not group:
            raise ValueError("group must not be empty")
        self._groups[group].add(job_id)
        self._membership[job_id].add(group)

    def remove_from_group(self, job_id: str, group: str) -> None:
        """Remove *job_id* from *group*.  No-op if not a member."""
        self._groups[group].discard(job_id)
        self._membership[job_id].discard(group)

    def disband_group(self, group: str) -> None:
        """Remove *group* and all its memberships."""
        for job_id in list(self._groups.get(group, [])):
            self._membership[job_id].discard(group)
        self._groups.pop(group, None)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def groups_for(self, job_id: str) -> List[str]:
        """Return sorted list of groups *job_id* belongs to."""
        return sorted(self._membership.get(job_id, set()))

    def members_of(self, group: str) -> List[str]:
        """Return sorted list of job IDs in *group*."""
        return sorted(self._groups.get(group, set()))

    def all_groups(self) -> List[str]:
        """Return sorted list of all known group names."""
        return sorted(k for k, v in self._groups.items() if v)

    def is_member(self, job_id: str, group: str) -> bool:
        """Return True if *job_id* is in *group*."""
        return job_id in self._groups.get(group, set())

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {g: sorted(ids) for g, ids in self._groups.items() if ids}

    @classmethod
    def from_dict(cls, data: dict) -> "JobGroupManager":
        mgr = cls()
        for group, job_ids in data.items():
            for jid in job_ids:
                mgr.add_to_group(jid, group)
        return mgr
