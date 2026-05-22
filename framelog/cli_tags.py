"""CLI entry-point for tag inspection: list tags on jobs loaded from a JSON export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from framelog.job_status import RenderJob, RenderStatus
from framelog.job_tags import JobTagManager


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="framelog-tags",
        description="Inspect or filter job tags from a JSON jobs file.",
    )
    p.add_argument("jobs_file", type=Path, help="Path to exported jobs JSON file.")
    sub = p.add_subparsers(dest="command", required=True)

    ls = sub.add_parser("list", help="List all tags in use.")
    ls.add_argument("--job", metavar="JOB_ID", help="Show tags for a specific job.")

    flt = sub.add_parser("filter", help="Print job IDs that match tag criteria.")
    flt.add_argument("--any", dest="any_tags", nargs="+", metavar="TAG",
                     help="Match jobs carrying ANY of these tags.")
    flt.add_argument("--all", dest="all_tags", nargs="+", metavar="TAG",
                     help="Match jobs carrying ALL of these tags.")
    return p


def _load_jobs(path: Path) -> List[RenderJob]:
    raw = json.loads(path.read_text())
    jobs = []
    for d in raw:
        job = RenderJob(
            job_id=d["job_id"],
            scene=d["scene"],
            server=d["server"],
            frame_range=tuple(d["frame_range"]),
        )
        job.status = RenderStatus(d["status"])
        job.error_message = d.get("error_message")
        # tags stored as extra field if present
        job._cli_tags = d.get("tags", [])
        jobs.append(job)
    return jobs


def run_tags(args: argparse.Namespace) -> None:
    jobs = _load_jobs(args.jobs_file)
    manager = JobTagManager()
    for job in jobs:
        manager.add_tags(job, getattr(job, "_cli_tags", []))

    if args.command == "list":
        if args.job:
            target = next((j for j in jobs if j.job_id == args.job), None)
            if target is None:
                print(f"Job '{args.job}' not found.", file=sys.stderr)
                sys.exit(1)
            tags = manager.get_tags(target)
            print(", ".join(sorted(tags)) if tags else "(no tags)")
        else:
            all_tags = manager.all_tags()
            if not all_tags:
                print("No tags found.")
            else:
                for tag in sorted(all_tags):
                    print(tag)

    elif args.command == "filter":
        if args.all_tags:
            result = manager.filter_by_tags_all(jobs, args.all_tags)
        elif args.any_tags:
            result = manager.filter_by_tags_any(jobs, args.any_tags)
        else:
            print("Provide --any or --all.", file=sys.stderr)
            sys.exit(1)
        for job in result:
            print(job.job_id)


def main() -> None:  # pragma: no cover
    run_tags(build_parser().parse_args())


if __name__ == "__main__":  # pragma: no cover
    main()
