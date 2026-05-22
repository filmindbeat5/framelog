"""CLI entry point for displaying job metrics from a JSON export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from framelog.job_exporter import jobs_to_dict_list
from framelog.job_metrics import compute_metrics
from framelog.job_registry import JobRegistry
from framelog.job_status import RenderJob, RenderStatus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-metrics",
        description="Display aggregate metrics for render jobs from a JSON export.",
    )
    parser.add_argument("input", metavar="FILE", help="Path to jobs JSON export file.")
    parser.add_argument(
        "--server",
        metavar="NAME",
        help="Show metrics only for a specific server.",
    )
    return parser


def _load_jobs_from_json(path: Path) -> list[RenderJob]:
    with path.open() as fh:
        data = json.load(fh)
    jobs = []
    for entry in data:
        job = RenderJob(
            job_id=entry["job_id"],
            scene=entry["scene"],
            frame_range=(entry["frame_start"], entry["frame_end"]),
            server=entry.get("server"),
        )
        job.status = RenderStatus(entry["status"])
        job.error_message = entry.get("error_message")
        jobs.append(job)
    return jobs


def run_metrics(args: argparse.Namespace) -> None:
    path = Path(args.input)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    jobs = _load_jobs_from_json(path)
    metrics = compute_metrics(jobs)

    print(f"Total jobs : {metrics.total_jobs}")
    print("Status breakdown:")
    for status, count in sorted(metrics.by_status.items()):
        print(f"  {status:<12} {count}")

    if metrics.overall_avg_duration_seconds is not None:
        print(f"Avg duration : {metrics.overall_avg_duration_seconds:.1f}s")

    servers = metrics.by_server
    if args.server:
        servers = {k: v for k, v in servers.items() if k == args.server}

    print("\nServer metrics:")
    for name, sm in sorted(servers.items()):
        avg = f"{sm.avg_duration_seconds:.1f}s" if sm.avg_duration_seconds is not None else "n/a"
        print(
            f"  {name:<20} total={sm.total}  completed={sm.completed}  "
            f"failed={sm.failed}  success={sm.success_rate:.0%}  avg={avg}"
        )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_metrics(args)


if __name__ == "__main__":
    main()
