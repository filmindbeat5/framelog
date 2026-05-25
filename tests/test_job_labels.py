"""Tests for framelog.job_labels."""

import pytest

from framelog.job_labels import JobLabelManager, LabelConflictError


@pytest.fixture()
def manager() -> JobLabelManager:
    return JobLabelManager()


def test_labels_for_unknown_job_is_empty(manager):
    assert manager.labels_for("job-x") == []


def test_resolve_unknown_label_is_none(manager):
    assert manager.resolve("unknown") is None


def test_assign_and_resolve(manager):
    manager.assign("job-1", "hero-shot")
    assert manager.resolve("hero-shot") == "job-1"


def test_labels_for_returns_assigned_labels(manager):
    manager.assign("job-1", "hero-shot")
    manager.assign("job-1", "final")
    assert manager.labels_for("job-1") == ["hero-shot", "final"]


def test_duplicate_assign_same_job_is_idempotent(manager):
    manager.assign("job-1", "hero-shot")
    manager.assign("job-1", "hero-shot")
    assert manager.labels_for("job-1") == ["hero-shot"]


def test_conflict_raises_when_label_taken_by_other_job(manager):
    manager.assign("job-1", "hero-shot")
    with pytest.raises(LabelConflictError):
        manager.assign("job-2", "hero-shot")


def test_unassign_removes_label(manager):
    manager.assign("job-1", "hero-shot")
    manager.unassign("hero-shot")
    assert manager.resolve("hero-shot") is None


def test_unassign_removes_label_from_job_list(manager):
    manager.assign("job-1", "hero-shot")
    manager.assign("job-1", "final")
    manager.unassign("hero-shot")
    assert manager.labels_for("job-1") == ["final"]


def test_unassign_nonexistent_is_noop(manager):
    manager.unassign("ghost")  # should not raise


def test_all_labels_returns_full_mapping(manager):
    manager.assign("job-1", "alpha")
    manager.assign("job-2", "beta")
    mapping = manager.all_labels()
    assert mapping == {"alpha": "job-1", "beta": "job-2"}


def test_all_labels_is_a_copy(manager):
    manager.assign("job-1", "alpha")
    copy = manager.all_labels()
    copy["alpha"] = "tampered"
    assert manager.resolve("alpha") == "job-1"


def test_empty_job_id_raises(manager):
    with pytest.raises(ValueError):
        manager.assign("", "label")


def test_empty_label_raises(manager):
    with pytest.raises(ValueError):
        manager.assign("job-1", "")


def test_reassign_same_label_to_same_job_after_unassign(manager):
    manager.assign("job-1", "hero-shot")
    manager.unassign("hero-shot")
    manager.assign("job-2", "hero-shot")  # now allowed
    assert manager.resolve("hero-shot") == "job-2"
