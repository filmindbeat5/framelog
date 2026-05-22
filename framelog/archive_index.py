"""Maintain a lightweight index of archive files for quick lookup."""

import json
import os
from datetime import datetime, timezone
from typing import List, Optional


INDEX_FILENAME = ".archive_index.json"


def _index_path(archive_dir: str) -> str:
    return os.path.join(archive_dir, INDEX_FILENAME)


def update_index(archive_dir: str, archive_path: str, job_count: int, label: str) -> None:
    """Append an entry to the archive directory index."""
    index_file = _index_path(archive_dir)
    entries = _read_index(archive_dir)

    entries.append(
        {
            "filename": os.path.basename(archive_path),
            "path": archive_path,
            "label": label,
            "job_count": job_count,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    with open(index_file, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2)


def _read_index(archive_dir: str) -> List[dict]:
    index_file = _index_path(archive_dir)
    if not os.path.isfile(index_file):
        return []
    with open(index_file, "r", encoding="utf-8") as fh:
        return json.load(fh)


def list_archives(archive_dir: str) -> List[dict]:
    """Return all index entries for the given archive directory."""
    return _read_index(archive_dir)


def find_archives_by_label(archive_dir: str, label: str) -> List[dict]:
    """Return index entries whose label matches."""
    return [e for e in _read_index(archive_dir) if e.get("label") == label]


def latest_archive(archive_dir: str) -> Optional[dict]:
    """Return the most recently created archive entry, or None."""
    entries = _read_index(archive_dir)
    if not entries:
        return None
    return max(entries, key=lambda e: e["created_at"])
