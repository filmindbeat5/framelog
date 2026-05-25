"""CLI for capturing and inspecting job snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from framelog.job_exporter import jobs_to_dict_list
from framelog.job_snapshots import JobSnapshot, JobSnapshotManager
from framelog.job_status import RenderJob, RenderStatus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-snapshots",
        description="Capture and inspect render job snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="Capture snapshots of all jobs in a JSON file.")
    cap.add_argument("jobs_file", help="Path to jobs JSON export.")
    cap.add_argument("--out", required=True, help="Output snapshot JSON file.")

    hist = sub.add_parser("history", help="Show snapshot history for a job.")
    hist.add_argument("snapshots_file", help="Path to snapshot JSON file.")
    hist.add_argument("job_id", help="Job ID to inspect.")

    diff = sub.add_parser("diff", help="Show field diffs between snapshots for a job.")
    diff.add_argument("snapshots_file", help="Path to snapshot JSON file.")
    diff.add_argument("job_id", help="Job ID to diff.")

    return parser


def _load_jobs(path: str) -> list[RenderJob]:
    data = json.loads(Path(path).read_text())
    jobs = []
    for d in data:
        job = RenderJob(
            job_id=d["job_id"],
            frame_start=d["frame_start"],
            frame_end=d["frame_end"],
            server=d.get("server"),
        )
        job.status = RenderStatus(d["status"])
        job.error_message = d.get("error_message")
        jobs.append(job)
    return jobs


def _manager_from_file(path: str) -> JobSnapshotManager:
    mgr = JobSnapshotManager()
    raw = json.loads(Path(path).read_text())
    for entry in raw:
        snap = JobSnapshot.from_dict(entry)
        mgr._snapshots.setdefault(snap.job_id, []).append(snap)
    return mgr


def run_snapshots(args: argparse.Namespace) -> int:
    if args.command == "capture":
        jobs = _load_jobs(args.jobs_file)
        mgr = JobSnapshotManager()
        all_snaps = [mgr.capture(j).to_dict() for j in jobs]
        Path(args.out).write_text(json.dumps(all_snaps, indent=2))
        print(f"Captured {len(all_snaps)} snapshot(s) -> {args.out}")
        return 0

    mgr = _manager_from_file(args.snapshots_file)

    if args.command == "history":
        history = mgr.history(args.job_id)
        if not history:
            print(f"No snapshots found for job '{args.job_id}'.")
            return 1
        for snap in history:
            print(json.dumps(snap.to_dict(), indent=2))
        return 0

    if args.command == "diff":
        diffs = mgr.diff(args.job_id)
        if not diffs:
            print(f"No diffs found for job '{args.job_id}'.")
            return 0
        print(json.dumps(diffs, indent=2))
        return 0

    return 1


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_snapshots(args))


if __name__ == "__main__":
    main()
