"""Archive completed or failed render jobs to persistent storage."""

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

from framelog.job_status import RenderJob, RenderStatus


DEFAULT_ARCHIVE_DIR = "archive"


def _archive_filename(label: str) -> str:
    """Generate a timestamped archive filename."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = label.replace(" ", "_").replace("/", "-")
    return f"{ts}_{safe_label}.json"


def archive_jobs(
    jobs: List[RenderJob],
    archive_dir: str = DEFAULT_ARCHIVE_DIR,
    label: str = "archive",
    statuses: Optional[List[RenderStatus]] = None,
) -> str:
    """Serialize matching jobs to a JSON file in archive_dir.

    Args:
        jobs: List of RenderJob instances to consider.
        archive_dir: Directory where the archive file will be written.
        label: Short label embedded in the filename.
        statuses: If provided, only jobs with these statuses are archived.

    Returns:
        Absolute path of the written archive file.
    """
    if statuses is not None:
        jobs = [j for j in jobs if j.status in statuses]

    os.makedirs(archive_dir, exist_ok=True)
    filename = _archive_filename(label)
    filepath = os.path.join(archive_dir, filename)

    records = [
        {
            "job_id": j.job_id,
            "server": j.server,
            "status": j.status.value,
            "frame_range": list(j.frame_range) if j.frame_range else None,
            "error_message": j.error_message,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        }
        for j in jobs
    ]

    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump({"archived_at": datetime.now(timezone.utc).isoformat(), "jobs": records}, fh, indent=2)

    return os.path.abspath(filepath)


def load_archive(filepath: str) -> List[dict]:
    """Load raw job records from an archive file."""
    with open(filepath, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("jobs", [])
