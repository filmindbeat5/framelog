"""CLI for inspecting job quota usage from a JSON job export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from framelog.job_quota import JobQuotaManager, QuotaPolicy
from framelog.job_status import RenderJob, RenderStatus


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="framelog-quota",
        description="Show running-job quota usage from a JSON job export.",
    )
    p.add_argument("jobs_json", help="Path to exported jobs JSON file")
    p.add_argument(
        "--global-max",
        type=int,
        default=100,
        metavar="N",
        help="Global running-job limit (default: 100)",
    )
    p.add_argument(
        "--server-max",
        type=int,
        default=20,
        metavar="N",
        help="Per-server running-job limit (default: 20)",
    )
    return p


def _load_jobs(path: str) -> list[RenderJob]:
    data = json.loads(Path(path).read_text())
    jobs: list[RenderJob] = []
    for entry in data:
        job = RenderJob(
            job_id=entry["job_id"],
            scene=entry.get("scene", ""),
            server=entry.get("server"),
            frame_range=tuple(entry.get("frame_range", [1, 1])),
        )
        try:
            job.status = RenderStatus[entry.get("status", "PENDING")]
        except KeyError:
            job.status = RenderStatus.PENDING
        jobs.append(job)
    return jobs


def run_quota(args: argparse.Namespace) -> int:
    try:
        jobs = _load_jobs(args.jobs_json)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error loading jobs: {exc}", file=sys.stderr)
        return 1

    policy = QuotaPolicy(
        global_max=args.global_max,
        per_server_max=args.server_max,
    )
    mgr = JobQuotaManager(policy=policy)
    mgr.rebuild(jobs)

    global_used = mgr.global_usage()
    print(f"Global running jobs : {global_used} / {policy.global_max}")

    server_usage = mgr.server_usage()
    if server_usage:
        print("\nPer-server usage:")
        for server, count in sorted(server_usage.items()):
            flag = " [OVER LIMIT]" if count >= policy.per_server_max else ""
            print(f"  {server}: {count} / {policy.per_server_max}{flag}")
    else:
        print("No running jobs on any server.")

    if global_used >= policy.global_max:
        print("\n[WARNING] Global running-job limit reached.")
        return 2

    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_quota(args))


if __name__ == "__main__":
    main()
