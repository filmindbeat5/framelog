"""Export render job reports to various output formats."""

import json
import csv
import io
from typing import List

from framelog.job_status import RenderJob
from framelog.job_reporter import JobReport


def jobs_to_dict_list(jobs: List[RenderJob]) -> List[dict]:
    """Convert a list of RenderJobs to serialisable dicts."""
    result = []
    for job in jobs:
        result.append({
            "job_id": job.job_id,
            "server_id": job.server_id,
            "status": job.status.value,
            "frame_start": job.frame_range[0],
            "frame_end": job.frame_range[1],
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        })
    return result


def export_jobs_to_json(jobs: List[RenderJob], indent: int = 2) -> str:
    """Serialise a list of RenderJobs to a JSON string."""
    return json.dumps(jobs_to_dict_list(jobs), indent=indent)


def export_jobs_to_csv(jobs: List[RenderJob]) -> str:
    """Serialise a list of RenderJobs to a CSV string."""
    fieldnames = [
        "job_id", "server_id", "status",
        "frame_start", "frame_end",
        "created_at", "started_at", "completed_at",
        "error_message",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in jobs_to_dict_list(jobs):
        writer.writerow(row)
    return output.getvalue()


def export_report_to_json(report: JobReport) -> str:
    """Serialise a JobReport summary to a JSON string."""
    data = {
        "generated_at": report.generated_at.isoformat(),
        "server_filter": report.server_filter,
        "total": report.total,
        "by_status": report.by_status,
        "by_server": report.by_server,
        "failed_messages": report.failed_messages,
    }
    return json.dumps(data, indent=2)
