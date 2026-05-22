"""Job watcher module for monitoring render job state transitions."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from framelog.job_status import RenderJob, RenderStatus


@dataclass
class StateTransitionEvent:
    """Represents a state transition event for a render job."""
    job_id: str
    previous_status: Optional[RenderStatus]
    new_status: RenderStatus
    message: Optional[str] = None


TransitionHandler = Callable[[StateTransitionEvent], None]


class JobWatcher:
    """Watches render jobs and triggers callbacks on status transitions."""

    def __init__(self) -> None:
        self._handlers: Dict[Optional[RenderStatus], List[TransitionHandler]] = {}
        self._job_snapshots: Dict[str, RenderStatus] = {}

    def on_transition(self, to_status: Optional[RenderStatus], handler: TransitionHandler) -> None:
        """Register a handler for transitions to a specific status.
        
        Pass None as to_status to handle all transitions.
        """
        self._handlers.setdefault(to_status, []).append(handler)

    def watch(self, job: RenderJob) -> None:
        """Record the current state of a job for future comparison."""
        self._job_snapshots[job.job_id] = job.status

    def check(self, job: RenderJob) -> List[StateTransitionEvent]:
        """Check a job for state changes and fire registered handlers.

        Returns a list of transition events that were detected.
        """
        previous = self._job_snapshots.get(job.job_id)
        current = job.status
        events: List[StateTransitionEvent] = []

        if previous != current:
            event = StateTransitionEvent(
                job_id=job.job_id,
                previous_status=previous,
                new_status=current,
                message=job.error_message,
            )
            events.append(event)
            self._fire(event)
            self._job_snapshots[job.job_id] = current

        return events

    def _fire(self, event: StateTransitionEvent) -> None:
        """Invoke all relevant handlers for a transition event."""
        for handler in self._handlers.get(event.new_status, []):
            handler(event)
        for handler in self._handlers.get(None, []):
            handler(event)

    def unwatch(self, job_id: str) -> None:
        """Stop tracking a job by its ID."""
        self._job_snapshots.pop(job_id, None)

    @property
    def watched_job_ids(self) -> List[str]:
        """Return the list of currently watched job IDs."""
        return list(self._job_snapshots.keys())
