"""Tests for framelog.job_groups."""

import pytest

from framelog.job_groups import JobGroupManager


@pytest.fixture()
def mgr() -> JobGroupManager:
    return JobGroupManager()


# ---------------------------------------------------------------------------
# Basic membership
# ---------------------------------------------------------------------------

def test_groups_for_unknown_job_is_empty(mgr):
    assert mgr.groups_for("job-x") == []


def test_members_of_unknown_group_is_empty(mgr):
    assert mgr.members_of("vfx") == []


def test_add_to_group_records_membership(mgr):
    mgr.add_to_group("j1", "vfx")
    assert "j1" in mgr.members_of("vfx")
    assert "vfx" in mgr.groups_for("j1")


def test_add_to_group_idempotent(mgr):
    mgr.add_to_group("j1", "vfx")
    mgr.add_to_group("j1", "vfx")
    assert mgr.members_of("vfx").count("j1") == 1


def test_job_can_belong_to_multiple_groups(mgr):
    mgr.add_to_group("j1", "vfx")
    mgr.add_to_group("j1", "priority")
    assert set(mgr.groups_for("j1")) == {"vfx", "priority"}


def test_multiple_jobs_in_same_group(mgr):
    mgr.add_to_group("j1", "batch")
    mgr.add_to_group("j2", "batch")
    assert set(mgr.members_of("batch")) == {"j1", "j2"}


# ---------------------------------------------------------------------------
# Removal
# ---------------------------------------------------------------------------

def test_remove_from_group(mgr):
    mgr.add_to_group("j1", "vfx")
    mgr.remove_from_group("j1", "vfx")
    assert "j1" not in mgr.members_of("vfx")
    assert "vfx" not in mgr.groups_for("j1")


def test_remove_noop_when_not_member(mgr):
    mgr.remove_from_group("j1", "vfx")  # should not raise


def test_disband_group_removes_all_members(mgr):
    mgr.add_to_group("j1", "temp")
    mgr.add_to_group("j2", "temp")
    mgr.disband_group("temp")
    assert mgr.members_of("temp") == []
    assert "temp" not in mgr.groups_for("j1")
    assert "temp" not in mgr.groups_for("j2")


def test_disband_nonexistent_group_noop(mgr):
    mgr.disband_group("ghost")  # should not raise


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def test_all_groups_returns_nonempty_groups(mgr):
    mgr.add_to_group("j1", "alpha")
    mgr.add_to_group("j2", "beta")
    assert set(mgr.all_groups()) == {"alpha", "beta"}


def test_all_groups_excludes_disbanded(mgr):
    mgr.add_to_group("j1", "temp")
    mgr.disband_group("temp")
    assert "temp" not in mgr.all_groups()


def test_is_member_true(mgr):
    mgr.add_to_group("j1", "g")
    assert mgr.is_member("j1", "g") is True


def test_is_member_false(mgr):
    assert mgr.is_member("j1", "g") is False


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_empty_job_id_raises(mgr):
    with pytest.raises(ValueError):
        mgr.add_to_group("", "g")


def test_empty_group_raises(mgr):
    with pytest.raises(ValueError):
        mgr.add_to_group("j1", "")


# ---------------------------------------------------------------------------
# Serialisation round-trip
# ---------------------------------------------------------------------------

def test_roundtrip(mgr):
    mgr.add_to_group("j1", "vfx")
    mgr.add_to_group("j2", "vfx")
    mgr.add_to_group("j1", "priority")
    restored = JobGroupManager.from_dict(mgr.to_dict())
    assert set(restored.members_of("vfx")) == {"j1", "j2"}
    assert "priority" in restored.groups_for("j1")
