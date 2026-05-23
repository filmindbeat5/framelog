"""Alert rules and notification hooks for render job status changes."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional
from framelog.job_status import RenderJob, RenderStatus


@dataclass
class AlertRule:
    """Defines a condition and a callback to invoke when matched."""
    name: str
    status_trigger: RenderStatus
    server_filter: Optional[str] = None  # None means any server
    callback: Optional[Callable[[RenderJob], None]] = None

    def matches(self, job: RenderJob) -> bool:
        if job.status != self.status_trigger:
            return False
        if self.server_filter and job.server_id != self.server_filter:
            return False
        return True


@dataclass
class AlertEvent:
    rule_name: str
    job_id: str
    server_id: Optional[str]
    status: RenderStatus
    message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "rule_name": self.rule_name,
            "job_id": self.job_id,
            "server_id": self.server_id,
            "status": self.status.value,
            "message": self.message,
        }


class JobAlertManager:
    """Evaluates alert rules against jobs and fires callbacks."""

    def __init__(self) -> None:
        self._rules: List[AlertRule] = []
        self._fired: List[AlertEvent] = []

    def add_rule(self, rule: AlertRule) -> None:
        self._rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != name]
        return len(self._rules) < before

    def evaluate(self, job: RenderJob) -> List[AlertEvent]:
        """Check all rules against *job* and fire matching callbacks."""
        triggered: List[AlertEvent] = []
        for rule in self._rules:
            if rule.matches(job):
                event = AlertEvent(
                    rule_name=rule.name,
                    job_id=job.job_id,
                    server_id=job.server_id,
                    status=job.status,
                    message=job.error_message,
                )
                self._fired.append(event)
                triggered.append(event)
                if rule.callback:
                    rule.callback(job)
        return triggered

    def fired_events(self) -> List[AlertEvent]:
        return list(self._fired)

    def clear_fired(self) -> None:
        self._fired.clear()
