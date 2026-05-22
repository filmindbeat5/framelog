"""CLI tool for inspecting and managing job dependencies."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from framelog.job_dependencies import CircularDependencyError, JobDependencyManager
from framelog.job_status import RenderJob


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-deps",
        description="Inspect and resolve render job dependencies.",
    )
    parser.add_argument("jobs_json", help="Path to exported jobs JSON file.")
    parser.add_argument(
        "--deps",
        metavar="CHILD:PARENT",
        nargs="+",
        default=[],
        help="Dependency pairs in CHILD:PARENT format (e.g. shot02:shot01).",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("order", help="Print jobs in topological execution order.")
    sub.add_parser("ready", help="Print jobs that are ready to run.")
    return parser


def _load_jobs(path: str) -> List[RenderJob]:
    data = json.loads(Path(path).read_text())
    jobs: List[RenderJob] = []
    for item in data:
        j = RenderJob(
            job_id=item["job_id"],
            scene=item.get("scene", ""),
            frame_range=tuple(item.get("frame_range", [1, 1])),
            server=item.get("server", ""),
        )
        j.status_str = item.get("status", "PENDING")
        jobs.append(j)
    return jobs


def _build_manager(dep_args: List[str]) -> JobDependencyManager:
    mgr = JobDependencyManager()
    for pair in dep_args:
        if ":" not in pair:
            print(f"[warn] Skipping malformed dep spec '{pair}' (expected CHILD:PARENT)",
                  file=sys.stderr)
            continue
        child, parent = pair.split(":", 1)
        try:
            mgr.add_dependency(child.strip(), parent.strip())
        except CircularDependencyError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            sys.exit(1)
    return mgr


def run_deps(args: argparse.Namespace) -> None:
    jobs = _load_jobs(args.jobs_json)
    mgr = _build_manager(args.deps)

    if args.command == "order":
        try:
            ordered_ids = mgr.topological_order([j.job_id for j in jobs])
        except CircularDependencyError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            sys.exit(1)
        print("Execution order:")
        for idx, jid in enumerate(ordered_ids, 1):
            print(f"  {idx:>3}. {jid}")

    elif args.command == "ready":
        ready = mgr.ready_jobs(jobs)
        if not ready:
            print("No jobs are currently ready to run.")
        else:
            print(f"{len(ready)} job(s) ready to run:")
            for j in ready:
                print(f"  - {j.job_id} (server={j.server})")

    else:
        # Default: show dependency summary
        print(f"Loaded {len(jobs)} job(s).")
        for j in jobs:
            deps = mgr.get_dependencies(j.job_id)
            if deps:
                print(f"  {j.job_id} depends on: {', '.join(sorted(deps))}")


def main() -> None:  # pragma: no cover
    run_deps(build_parser().parse_args())


if __name__ == "__main__":  # pragma: no cover
    main()
