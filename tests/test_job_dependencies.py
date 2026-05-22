"""Tests for framelog.job_dependencies."""

import pytest

from framelog.job_dependencies import CircularDependencyError, JobDependencyManager
from framelog.job_status import RenderJob, RenderStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mgr() -> JobDependencyManager:
    return JobDependencyManager()


def _job(job_id: str, status: RenderStatus = RenderStatus.PENDING) -> RenderJob:
    j = RenderJob(job_id=job_id, scene="scene.blend", frame_range=(1, 10), server="srv1")
    j.status = status
    return j


# ---------------------------------------------------------------------------
# add / remove
# ---------------------------------------------------------------------------

def test_add_dependency_recorded(mgr):
    mgr.add_dependency("B", "A")
    assert "A" in mgr.get_dependencies("B")


def test_remove_dependency(mgr):
    mgr.add_dependency("B", "A")
    mgr.remove_dependency("B", "A")
    assert "A" not in mgr.get_dependencies("B")


def test_self_dependency_raises(mgr):
    with pytest.raises(ValueError):
        mgr.add_dependency("A", "A")


def test_circular_dependency_raises(mgr):
    mgr.add_dependency("B", "A")
    mgr.add_dependency("C", "B")
    with pytest.raises(CircularDependencyError):
        mgr.add_dependency("A", "C")


def test_circular_dependency_not_stored(mgr):
    mgr.add_dependency("B", "A")
    try:
        mgr.add_dependency("A", "B")
    except CircularDependencyError:
        pass
    assert "B" not in mgr.get_dependencies("A")


# ---------------------------------------------------------------------------
# is_ready / ready_jobs
# ---------------------------------------------------------------------------

def test_job_with_no_deps_is_ready(mgr):
    job = _job("A")
    assert mgr.is_ready(job, [job]) is True


def test_job_not_ready_when_dep_pending(mgr):
    a = _job("A", RenderStatus.PENDING)
    b = _job("B", RenderStatus.PENDING)
    mgr.add_dependency("B", "A")
    assert mgr.is_ready(b, [a, b]) is False


def test_job_ready_when_dep_completed(mgr):
    a = _job("A", RenderStatus.COMPLETED)
    b = _job("B", RenderStatus.PENDING)
    mgr.add_dependency("B", "A")
    assert mgr.is_ready(b, [a, b]) is True


def test_ready_jobs_returns_only_pending_satisfied(mgr):
    a = _job("A", RenderStatus.COMPLETED)
    b = _job("B", RenderStatus.PENDING)
    c = _job("C", RenderStatus.PENDING)
    mgr.add_dependency("B", "A")
    mgr.add_dependency("C", "B")  # C still waiting for B
    ready = mgr.ready_jobs([a, b, c])
    assert b in ready
    assert c not in ready
    assert a not in ready  # already completed, not pending


# ---------------------------------------------------------------------------
# topological_order
# ---------------------------------------------------------------------------

def test_topological_order_simple(mgr):
    mgr.add_dependency("B", "A")
    mgr.add_dependency("C", "B")
    order = mgr.topological_order(["A", "B", "C"])
    assert order.index("A") < order.index("B") < order.index("C")


def test_topological_order_no_deps(mgr):
    order = mgr.topological_order(["X", "Y", "Z"])
    assert set(order) == {"X", "Y", "Z"}


def test_topological_order_cycle_raises(mgr):
    # Manually corrupt state to simulate a cycle without add_dependency guard
    mgr._deps["A"].add("B")
    mgr._deps["B"].add("A")
    with pytest.raises(CircularDependencyError):
        mgr.topological_order(["A", "B"])
