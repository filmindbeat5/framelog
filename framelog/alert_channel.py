"""Pluggable notification channels for alert events."""

from abc import ABC, abstractmethod
from typing import List
from framelog.job_alerts import AlertEvent


class AlertChannel(ABC):
    """Base class for all notification channels."""

    @abstractmethod
    def send(self, event: AlertEvent) -> None:
        """Dispatch *event* through this channel."""


class InMemoryChannel(AlertChannel):
    """Stores events in memory — useful for testing and inspection."""

    def __init__(self) -> None:
        self._messages: List[str] = []
        self._events: List[AlertEvent] = []

    def send(self, event: AlertEvent) -> None:
        msg = (
            f"[ALERT] rule={event.rule_name} job={event.job_id} "
            f"server={event.server_id} status={event.status.value}"
        )
        if event.message:
            msg += f" msg={event.message!r}"
        self._messages.append(msg)
        self._events.append(event)

    def messages(self) -> List[str]:
        return list(self._messages)

    def events(self) -> List[AlertEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._messages.clear()
        self._events.clear()


class LogFileChannel(AlertChannel):
    """Appends alert events to a plain-text log file."""

    def __init__(self, filepath: str) -> None:
        self._filepath = filepath

    def send(self, event: AlertEvent) -> None:
        import datetime
        ts = datetime.datetime.utcnow().isoformat()
        line = (
            f"{ts} ALERT rule={event.rule_name} job={event.job_id} "
            f"server={event.server_id} status={event.status.value}"
        )
        if event.message:
            line += f" error={event.message!r}"
        with open(self._filepath, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


class MultiChannel(AlertChannel):
    """Fan-out channel that forwards events to multiple sub-channels."""

    def __init__(self, channels: List[AlertChannel] | None = None) -> None:
        self._channels: List[AlertChannel] = list(channels or [])

    def add(self, channel: AlertChannel) -> None:
        self._channels.append(channel)

    def send(self, event: AlertEvent) -> None:
        for ch in self._channels:
            ch.send(event)
