"""Tests for JobAuditManager."""

import pytest
from datetime import timezone
from framelog.job_audit import AuditEntry, JobAuditManager


@pytest.fixture
def manager():
    return JobAuditManager()


def test_record_returns_entry(manager):
    entry = manager.record("job-1", "start", "scheduler")
    assert isinstance(entry, AuditEntry)
    assert entry.job_id == "job-1"
    assert entry.action == "start"
    assert entry.actor == "scheduler"
    assert entry.detail is None


def test_record_with_detail(manager):
    entry = manager.record("job-2", "fail", "worker-3", detail="Out of memory")
    assert entry.detail == "Out of memory"


def test_record_empty_job_id_raises(manager):
    with pytest.raises(ValueError, match="job_id"):
        manager.record("", "start", "scheduler")


def test_record_empty_action_raises(manager):
    with pytest.raises(ValueError, match="action"):
        manager.record("job-1", "", "scheduler")


def test_record_empty_actor_raises(manager):
    with pytest.raises(ValueError, match="actor"):
        manager.record("job-1", "start", "")


def test_entries_for_job(manager):
    manager.record("job-1", "start", "sched")
    manager.record("job-2", "start", "sched")
    manager.record("job-1", "complete", "worker-1")
    result = manager.entries_for_job("job-1")
    assert len(result) == 2
    assert all(e.job_id == "job-1" for e in result)


def test_entries_by_actor(manager):
    manager.record("job-1", "start", "sched")
    manager.record("job-2", "retry", "ops")
    manager.record("job-3", "complete", "sched")
    result = manager.entries_by_actor("sched")
    assert len(result) == 2


def test_entries_by_action(manager):
    manager.record("job-1", "start", "sched")
    manager.record("job-2", "start", "sched")
    manager.record("job-3", "fail", "worker")
    result = manager.entries_by_action("start")
    assert len(result) == 2


def test_all_entries(manager):
    manager.record("job-1", "start", "sched")
    manager.record("job-2", "fail", "worker")
    assert len(manager.all_entries()) == 2


def test_to_dict_list_keys(manager):
    manager.record("job-1", "start", "sched", detail="initial run")
    entries = manager.to_dict_list()
    assert len(entries) == 1
    d = entries[0]
    assert set(d.keys()) == {"job_id", "action", "actor", "timestamp", "detail"}


def test_roundtrip_serialisation(manager):
    manager.record("job-1", "start", "sched")
    manager.record("job-2", "complete", "worker-2", detail="ok")
    data = manager.to_dict_list()
    new_manager = JobAuditManager()
    new_manager.load_from_dict_list(data)
    restored = new_manager.all_entries()
    assert len(restored) == 2
    assert restored[0].job_id == "job-1"
    assert restored[1].detail == "ok"


def test_grouped_by_job(manager):
    manager.record("job-1", "start", "sched")
    manager.record("job-1", "complete", "worker")
    manager.record("job-2", "start", "sched")
    grouped = manager.grouped_by_job()
    assert set(grouped.keys()) == {"job-1", "job-2"}
    assert len(grouped["job-1"]) == 2
    assert len(grouped["job-2"]) == 1


def test_timestamp_is_utc(manager):
    entry = manager.record("job-1", "start", "sched")
    assert entry.timestamp.tzinfo == timezone.utc
