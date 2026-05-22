"""Tracks inter-job dependencies and resolves execution order."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set

from framelog.job_status import RenderJob, RenderStatus


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""


class JobDependencyManager:
    """Manages prerequisite relationships between render jobs."""

    def __init__(self) -> None:
        # job_id -> set of job_ids that must complete before it
        self._deps: Dict[str, Set[str]] = defaultdict(set)

    def add_dependency(self, job_id: str, depends_on: str) -> None:
        """Declare that *job_id* must wait for *depends_on* to complete."""
        if job_id == depends_on:
            raise ValueError(f"Job '{job_id}' cannot depend on itself.")
        self._deps[job_id].add(depends_on)
        if self._has_cycle(job_id):
            self._deps[job_id].discard(depends_on)
            raise CircularDependencyError(
                f"Adding dependency '{job_id}' -> '{depends_on}' creates a cycle."
            )

    def remove_dependency(self, job_id: str, depends_on: str) -> None:
        """Remove a previously registered dependency."""
        self._deps[job_id].discard(depends_on)

    def get_dependencies(self, job_id: str) -> Set[str]:
        """Return the set of job IDs that *job_id* directly depends on."""
        return set(self._deps.get(job_id, set()))

    def is_ready(self, job: RenderJob, all_jobs: List[RenderJob]) -> bool:
        """Return True if all dependencies of *job* have completed successfully."""
        completed_ids = {
            j.job_id for j in all_jobs if j.status == RenderStatus.COMPLETED
        }
        return self._deps[job.job_id].issubset(completed_ids)

    def ready_jobs(self, jobs: List[RenderJob]) -> List[RenderJob]:
        """Return pending jobs whose dependencies are all satisfied."""
        return [
            j for j in jobs
            if j.status == RenderStatus.PENDING and self.is_ready(j, jobs)
        ]

    def topological_order(self, job_ids: List[str]) -> List[str]:
        """Return *job_ids* sorted so dependencies come before dependents."""
        id_set = set(job_ids)
        in_degree: Dict[str, int] = {jid: 0 for jid in job_ids}
        for jid in job_ids:
            for dep in self._deps[jid]:
                if dep in id_set:
                    in_degree[jid] += 1

        queue: deque[str] = deque(jid for jid, deg in in_degree.items() if deg == 0)
        order: List[str] = []
        while queue:
            current = queue.popleft()
            order.append(current)
            for jid in job_ids:
                if current in self._deps[jid]:
                    in_degree[jid] -= 1
                    if in_degree[jid] == 0:
                        queue.append(jid)

        if len(order) != len(job_ids):
            raise CircularDependencyError("Cycle detected during topological sort.")
        return order

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _has_cycle(self, start: str) -> bool:
        visited: Set[str] = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in visited:
                return True
            visited.add(node)
            stack.extend(self._deps.get(node, set()))
        return False
