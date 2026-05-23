"""Tests for framelog.job_checkpoints."""

import pytest
from datetime import timezone

from framelog.job_checkpoints import Checkpoint, JobCheckpointManager


@pytest.fixture
def manager() -> JobCheckpointManager:
    return JobCheckpointManager()


# ---------------------------------------------------------------------------
# Checkpoint dataclass
# ---------------------------------------------------------------------------

def test_checkpoint_to_dict_keys():
    cp = Checkpoint(label="halfway", frame=50)
    d = cp.to_dict()
    assert set(d.keys()) == {"label", "frame", "timestamp", "note"}


def test_checkpoint_roundtrip():
    cp = Checkpoint(label="done", frame=100, note="all clear")
    restored = Checkpoint.from_dict(cp.to_dict())
    assert restored.label == cp.label
    assert restored.frame == cp.frame
    assert restored.note == cp.note
    assert restored.timestamp.tzinfo == timezone.utc


# ---------------------------------------------------------------------------
# Adding checkpoints
# ---------------------------------------------------------------------------

def test_add_checkpoint_returns_checkpoint(manager):
    cp = manager.add_checkpoint("job-1", "start", frame=0)
    assert isinstance(cp, Checkpoint)
    assert cp.label == "start"
    assert cp.frame == 0


def test_add_checkpoint_empty_label_raises(manager):
    with pytest.raises(ValueError, match="label"):
        manager.add_checkpoint("job-1", "", frame=10)


def test_multiple_checkpoints_ordered(manager):
    manager.add_checkpoint("job-1", "quarter", frame=25)
    manager.add_checkpoint("job-1", "half", frame=50)
    manager.add_checkpoint("job-1", "done", frame=100)
    cps = manager.get_checkpoints("job-1")
    assert [c.label for c in cps] == ["quarter", "half", "done"]


# ---------------------------------------------------------------------------
# Retrieval helpers
# ---------------------------------------------------------------------------

def test_get_checkpoints_empty_for_unknown_job(manager):
    assert manager.get_checkpoints("no-such-job") == []


def test_latest_checkpoint_returns_last(manager):
    manager.add_checkpoint("job-2", "a", frame=10)
    manager.add_checkpoint("job-2", "b", frame=20)
    latest = manager.latest_checkpoint("job-2")
    assert latest is not None
    assert latest.label == "b"


def test_latest_checkpoint_none_when_no_checkpoints(manager):
    assert manager.latest_checkpoint("ghost") is None


# ---------------------------------------------------------------------------
# Clearing and listing
# ---------------------------------------------------------------------------

def test_clear_checkpoints_returns_count(manager):
    manager.add_checkpoint("job-3", "x", frame=1)
    manager.add_checkpoint("job-3", "y", frame=2)
    removed = manager.clear_checkpoints("job-3")
    assert removed == 2
    assert manager.get_checkpoints("job-3") == []


def test_clear_nonexistent_job_returns_zero(manager):
    assert manager.clear_checkpoints("nope") == 0


def test_all_job_ids_lists_jobs_with_checkpoints(manager):
    manager.add_checkpoint("job-a", "start", frame=0)
    manager.add_checkpoint("job-b", "start", frame=0)
    ids = manager.all_job_ids()
    assert "job-a" in ids
    assert "job-b" in ids


def test_all_job_ids_excludes_cleared_jobs(manager):
    manager.add_checkpoint("job-c", "start", frame=0)
    manager.clear_checkpoints("job-c")
    assert "job-c" not in manager.all_job_ids()
