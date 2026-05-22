"""Dispatches jobs from the scheduler to registered servers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from framelog.job_registry import JobRegistry
from framelog.job_scheduler import JobScheduler
from framelog.job_status import RenderJob


DispatchHandler = Callable[[RenderJob, str], bool]


@dataclass
class DispatchResult:
    job_id: str
    server: str
    success: bool
    error: Optional[str] = None


class JobDispatcher:
    """Pulls jobs from the scheduler and dispatches them to available servers."""

    def __init__(
        self,
        scheduler: JobScheduler,
        registry: JobRegistry,
        handler: Optional[DispatchHandler] = None,
    ) -> None:
        self._scheduler = scheduler
        self._registry = registry
        self._handler: DispatchHandler = handler or self._default_handler
        self._available_servers: List[str] = []
        self._history: List[DispatchResult] = []

    def register_server(self, server_id: str) -> None:
        if server_id not in self._available_servers:
            self._available_servers.append(server_id)

    def unregister_server(self, server_id: str) -> None:
        self._available_servers = [s for s in self._available_servers if s != server_id]

    def dispatch_next(self) -> Optional[DispatchResult]:
        """Dispatch the next queued job to the first available server."""
        if not self._available_servers:
            return None
        job = self._scheduler.dequeue()
        if job is None:
            return None
        server = self._available_servers[0]
        try:
            ok = self._handler(job, server)
            if ok:
                job.start()
            result = DispatchResult(job_id=job.job_id, server=server, success=ok)
        except Exception as exc:  # noqa: BLE001
            result = DispatchResult(
                job_id=job.job_id, server=server, success=False, error=str(exc)
            )
        self._history.append(result)
        return result

    def dispatch_all(self) -> List[DispatchResult]:
        """Dispatch all queued jobs in priority order."""
        results: List[DispatchResult] = []
        while not self._scheduler.is_empty():
            r = self.dispatch_next()
            if r is None:
                break
            results.append(r)
        return results

    def history(self) -> List[DispatchResult]:
        return list(self._history)

    @staticmethod
    def _default_handler(job: RenderJob, server: str) -> bool:  # noqa: ARG004
        return True
