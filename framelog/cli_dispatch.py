"""CLI entry point for scheduling and dispatching render jobs."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from framelog.job_dispatcher import JobDispatcher
from framelog.job_registry import JobRegistry
from framelog.job_scheduler import JobScheduler
from framelog.job_status import RenderJob


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-dispatch",
        description="Schedule and dispatch render jobs from a JSON manifest.",
    )
    parser.add_argument(
        "manifest", help="Path to JSON file containing job definitions."
    )
    parser.add_argument(
        "--servers",
        nargs="+",
        default=["render-01"],
        metavar="SERVER",
        help="Server IDs to dispatch jobs to (default: render-01).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print dispatch plan without executing.",
    )
    return parser


def _load_jobs(manifest_path: str) -> List[RenderJob]:
    with open(manifest_path) as fh:
        data = json.load(fh)
    jobs = []
    for entry in data:
        job = RenderJob(
            job_id=entry["job_id"],
            scene=entry["scene"],
            frame_range=tuple(entry["frame_range"]),
            server=entry.get("server", "unassigned"),
        )
        jobs.append((job, int(entry.get("priority", 10))))
    return jobs


def run_dispatch(args: argparse.Namespace) -> int:
    try:
        job_entries = _load_jobs(args.manifest)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        print(f"[error] Failed to load manifest: {exc}", file=sys.stderr)
        return 1

    scheduler = JobScheduler()
    registry = JobRegistry()
    dispatcher = JobDispatcher(scheduler, registry)

    for server in args.servers:
        dispatcher.register_server(server)

    for job, priority in job_entries:
        registry.register(job)
        scheduler.enqueue(job, priority=priority)

    if args.dry_run:
        print(f"[dry-run] {scheduler.pending_count()} job(s) queued for dispatch.")
        for job in scheduler.all_scheduled():
            print(f"  - {job.job_id} | scene={job.scene} | frames={job.frame_range}")
        return 0

    results = dispatcher.dispatch_all()
    ok = sum(1 for r in results if r.success)
    fail = len(results) - ok
    print(f"Dispatched {ok} job(s) successfully, {fail} failed.")
    for r in results:
        status = "OK" if r.success else f"FAIL ({r.error})"
        print(f"  [{status}] {r.job_id} -> {r.server}")
    return 0 if fail == 0 else 1


def main() -> None:  # pragma: no cover
    parser = build_parser()
    sys.exit(run_dispatch(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
