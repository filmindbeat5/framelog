"""Tests for framelog.job_alerts."""

import pytest
from framelog.job_status import RenderJob, RenderStatus, fail, complete, start
from framelog.job_alerts import AlertRule, AlertEvent, JobAlertManager


@pytest.fixture
def manager() -> JobAlertManager:
    return JobAlertManager()


def _failed_job(job_id: str = "job-1", server_id: str = "srv-a") -> RenderJob:
    job = RenderJob(job_id=job_id, scene_file="scene.blend",
                    frame_range=(1, 10), server_id=server_id)
    fail(job, "render crashed")
    return job


def _completed_job(job_id: str = "job-2", server_id: str = "srv-a") -> RenderJob:
    job = RenderJob(job_id=job_id, scene_file="scene.blend",
                    frame_range=(1, 10), server_id=server_id)
    start(job)
    complete(job)
    return job


def test_no_rules_no_events(manager):
    events = manager.evaluate(_failed_job())
    assert events == []


def test_matching_status_triggers_event(manager):
    rule = AlertRule(name="fail-alert", status_trigger=RenderStatus.FAILED)
    manager.add_rule(rule)
    events = manager.evaluate(_failed_job())
    assert len(events) == 1
    assert events[0].rule_name == "fail-alert"


def test_non_matching_status_no_event(manager):
    rule = AlertRule(name="fail-alert", status_trigger=RenderStatus.FAILED)
    manager.add_rule(rule)
    events = manager.evaluate(_completed_job())
    assert events == []


def test_server_filter_matches(manager):
    rule = AlertRule(name="srv-fail", status_trigger=RenderStatus.FAILED,
                     server_filter="srv-a")
    manager.add_rule(rule)
    events = manager.evaluate(_failed_job(server_id="srv-a"))
    assert len(events) == 1


def test_server_filter_no_match(manager):
    rule = AlertRule(name="srv-fail", status_trigger=RenderStatus.FAILED,
                     server_filter="srv-b")
    manager.add_rule(rule)
    events = manager.evaluate(_failed_job(server_id="srv-a"))
    assert events == []


def test_callback_is_called(manager):
    called_with = []
    rule = AlertRule(name="cb-rule", status_trigger=RenderStatus.FAILED,
                     callback=lambda j: called_with.append(j.job_id))
    manager.add_rule(rule)
    job = _failed_job()
    manager.evaluate(job)
    assert called_with == [job.job_id]


def test_fired_events_accumulate(manager):
    rule = AlertRule(name="fail-alert", status_trigger=RenderStatus.FAILED)
    manager.add_rule(rule)
    manager.evaluate(_failed_job("j1"))
    manager.evaluate(_failed_job("j2"))
    assert len(manager.fired_events()) == 2


def test_clear_fired(manager):
    rule = AlertRule(name="fail-alert", status_trigger=RenderStatus.FAILED)
    manager.add_rule(rule)
    manager.evaluate(_failed_job())
    manager.clear_fired()
    assert manager.fired_events() == []


def test_remove_rule(manager):
    rule = AlertRule(name="fail-alert", status_trigger=RenderStatus.FAILED)
    manager.add_rule(rule)
    removed = manager.remove_rule("fail-alert")
    assert removed is True
    events = manager.evaluate(_failed_job())
    assert events == []


def test_remove_nonexistent_rule_returns_false(manager):
    assert manager.remove_rule("ghost") is False


def test_alert_event_to_dict():
    event = AlertEvent(rule_name="r", job_id="j", server_id="s",
                       status=RenderStatus.FAILED, message="oops")
    d = event.to_dict()
    assert d["rule_name"] == "r"
    assert d["status"] == "failed"
    assert d["message"] == "oops"
