"""Tests for framelog.alert_channel."""

import os
import tempfile
import pytest
from framelog.job_status import RenderStatus
from framelog.job_alerts import AlertEvent
from framelog.alert_channel import InMemoryChannel, LogFileChannel, MultiChannel


@pytest.fixture
def event() -> AlertEvent:
    return AlertEvent(
        rule_name="fail-rule",
        job_id="job-99",
        server_id="srv-x",
        status=RenderStatus.FAILED,
        message="segfault",
    )


def test_in_memory_channel_stores_message(event):
    ch = InMemoryChannel()
    ch.send(event)
    msgs = ch.messages()
    assert len(msgs) == 1
    assert "job-99" in msgs[0]
    assert "fail-rule" in msgs[0]


def test_in_memory_channel_stores_event(event):
    ch = InMemoryChannel()
    ch.send(event)
    assert ch.events()[0] is event


def test_in_memory_channel_includes_error_message(event):
    ch = InMemoryChannel()
    ch.send(event)
    assert "segfault" in ch.messages()[0]


def test_in_memory_channel_clear(event):
    ch = InMemoryChannel()
    ch.send(event)
    ch.clear()
    assert ch.messages() == []
    assert ch.events() == []


def test_log_file_channel_creates_file(event):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "alerts.log")
        ch = LogFileChannel(path)
        ch.send(event)
        assert os.path.exists(path)


def test_log_file_channel_content(event):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "alerts.log")
        ch = LogFileChannel(path)
        ch.send(event)
        content = open(path).read()
        assert "job-99" in content
        assert "segfault" in content


def test_log_file_channel_appends(event):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "alerts.log")
        ch = LogFileChannel(path)
        ch.send(event)
        ch.send(event)
        lines = open(path).readlines()
        assert len(lines) == 2


def test_multi_channel_fans_out(event):
    ch1 = InMemoryChannel()
    ch2 = InMemoryChannel()
    multi = MultiChannel([ch1, ch2])
    multi.send(event)
    assert len(ch1.events()) == 1
    assert len(ch2.events()) == 1


def test_multi_channel_add(event):
    ch1 = InMemoryChannel()
    multi = MultiChannel()
    multi.add(ch1)
    multi.send(event)
    assert len(ch1.events()) == 1
