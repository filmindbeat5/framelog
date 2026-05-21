"""Simple CLI entry point for printing render job reports."""

import argparse
import sys

from framelog.job_registry import JobRegistry
from framelog.job_reporter import generate_report, format_report
from framelog.job_exporter import export_report_to_json, export_jobs_to_csv, export_jobs_to_json
from framelog.job_filter import filter_by_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-report",
        description="Print a summary report of render jobs.",
    )
    parser.add_argument(
        "--server",
        metavar="SERVER_ID",
        help="Filter report to a specific server.",
        default=None,
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def run_report(registry: JobRegistry, args=None, out=None) -> int:
    """Run the report command against a registry. Returns exit code."""
    if out is None:
        out = sys.stdout

    parser = build_parser()
    parsed = parser.parse_args(args or [])

    report = generate_report(registry, server=parsed.server)
    jobs = registry.all_jobs()
    if parsed.server:
        jobs = filter_by_server(jobs, parsed.server)

    if parsed.format == "text":
        out.write(format_report(report) + "\n")
    elif parsed.format == "json":
        out.write(export_report_to_json(report) + "\n")
    elif parsed.format == "csv":
        out.write(export_jobs_to_csv(jobs))
    else:
        parser.print_help(out)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    from framelog.job_registry import JobRegistry as _R
    sys.exit(run_report(_R()))
