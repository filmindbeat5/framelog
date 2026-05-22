"""CLI entry point for archiving render jobs from a JSON export."""

import argparse
import json
import sys
from typing import List

from framelog.job_status import RenderJob, RenderStatus
from framelog.job_archiver import archive_jobs, DEFAULT_ARCHIVE_DIR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-archive",
        description="Archive render jobs from a JSON export file.",
    )
    parser.add_argument("input", help="Path to jobs JSON export file.")
    parser.add_argument(
        "--archive-dir",
        default=DEFAULT_ARCHIVE_DIR,
        help=f"Destination directory for archive files (default: {DEFAULT_ARCHIVE_DIR}).",
    )
    parser.add_argument(
        "--label",
        default="archive",
        help="Label embedded in the archive filename.",
    )
    parser.add_argument(
        "--status",
        nargs="+",
        choices=[s.value for s in RenderStatus],
        default=None,
        help="Only archive jobs with these statuses.",
    )
    return parser


def _load_jobs(filepath: str) -> List[RenderJob]:
    """Reconstruct RenderJob instances from a JSON export."""
    with open(filepath, "r", encoding="utf-8") as fh:
        records = json.load(fh)

    jobs = []
    for r in records:
        job = RenderJob(
            job_id=r["job_id"],
            server=r["server"],
            frame_range=range(*r["frame_range"]) if r.get("frame_range") else None,
        )
        job.status = RenderStatus(r["status"])
        job.error_message = r.get("error_message")
        jobs.append(job)
    return jobs


def run_archive(args: argparse.Namespace) -> int:
    try:
        jobs = _load_jobs(args.input)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error loading input file: {exc}", file=sys.stderr)
        return 1

    statuses = [RenderStatus(s) for s in args.status] if args.status else None

    output_path = archive_jobs(
        jobs,
        archive_dir=args.archive_dir,
        label=args.label,
        statuses=statuses,
    )
    print(f"Archived {len(jobs)} job(s) → {output_path}")
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_archive(args))


if __name__ == "__main__":
    main()
