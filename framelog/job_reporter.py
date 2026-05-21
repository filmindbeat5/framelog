"""Report generation utilities for render job summaries."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from framelog.job_status import RenderJob, RenderStatus
from framelog.job_registry import JobRegistry
from framelog.job_filter import filter_by_status, filter_by_server, group_by_status


@dataclass
class JobReport:
    """Summary report for a set of render jobs."""
    generated_at: datetime = field(default_factory=datetime.utcnow)
    total: int = 0
    by_status: Dict[str, int] = field(default_factory=dict)
    by_server: Dict[str, int] = field(default_factory=dict)
    failed_messages: List[str] = field(default_factory=list)
    server_filter: Optional[str] = None

    def summary_line(self) -> str:
        parts = [f"Total: {self.total}"]
        for status, count in self.by_status.items():
            parts.append(f"{status}: {count}")
        return " | ".join(parts)


def generate_report(
    registry: JobRegistry,
    server: Optional[str] = None,
) -> JobReport:
    """Generate a JobReport from a registry, optionally filtered by server."""
    jobs = registry.all_jobs()

    if server:
        jobs = filter_by_server(jobs, server)

    report = JobReport(server_filter=server)
    report.total = len(jobs)

    grouped = group_by_status(jobs)
    report.by_status = {status.value: len(job_list) for status, job_list in grouped.items()}

    server_map: Dict[str, int] = {}
    for job in jobs:
        server_map[job.server_id] = server_map.get(job.server_id, 0) + 1
    report.by_server = server_map

    failed = filter_by_status(jobs, RenderStatus.FAILED)
    report.failed_messages = [
        f"[{job.job_id}] {job.error_message}" for job in failed if job.error_message
    ]

    return report


def format_report(report: JobReport) -> str:
    """Format a JobReport as a human-readable string."""
    lines = [
        f"=== Render Job Report ===",
        f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
    ]
    if report.server_filter:
        lines.append(f"Server filter: {report.server_filter}")
    lines.append(f"Total jobs: {report.total}")
    lines.append("Status breakdown:")
    for status, count in sorted(report.by_status.items()):
        lines.append(f"  {status}: {count}")
    lines.append("Jobs per server:")
    for srv, count in sorted(report.by_server.items()):
        lines.append(f"  {srv}: {count}")
    if report.failed_messages:
        lines.append("Failed job errors:")
        for msg in report.failed_messages:
            lines.append(f"  {msg}")
    return "\n".join(lines)
