"""Persistent JSON-backed store for JobSnapshotManager state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from framelog.job_snapshots import JobSnapshot, JobSnapshotManager

_DEFAULT_FILENAME = "snapshots.json"


def _store_path(directory: str, filename: str = _DEFAULT_FILENAME) -> Path:
    return Path(directory) / filename


def save_manager(mgr: JobSnapshotManager, directory: str, filename: str = _DEFAULT_FILENAME) -> Path:
    """Serialise all snapshots in *mgr* to a JSON file and return its path."""
    path = _store_path(directory, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    all_snaps = [
        snap.to_dict()
        for snaps in mgr._snapshots.values()
        for snap in snaps
    ]
    path.write_text(json.dumps(all_snaps, indent=2))
    return path


def load_manager(directory: str, filename: str = _DEFAULT_FILENAME) -> JobSnapshotManager:
    """Load a JobSnapshotManager from a JSON file, or return an empty one."""
    path = _store_path(directory, filename)
    mgr = JobSnapshotManager()
    if not path.exists():
        return mgr
    raw = json.loads(path.read_text())
    for entry in raw:
        snap = JobSnapshot.from_dict(entry)
        mgr._snapshots.setdefault(snap.job_id, []).append(snap)
    return mgr


def merge_manager(
    base: JobSnapshotManager,
    incoming: JobSnapshotManager,
) -> JobSnapshotManager:
    """Merge *incoming* snapshots into *base*, preserving chronological order."""
    merged = JobSnapshotManager()
    all_ids = set(base._snapshots) | set(incoming._snapshots)
    for job_id in all_ids:
        combined = base.history(job_id) + incoming.history(job_id)
        combined.sort(key=lambda s: s.captured_at)
        merged._snapshots[job_id] = combined
    return merged
