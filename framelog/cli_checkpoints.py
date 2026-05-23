"""CLI for inspecting render-job checkpoints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from framelog.job_checkpoints import JobCheckpointManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-checkpoints",
        description="Inspect checkpoints for render jobs.",
    )
    parser.add_argument(
        "--data",
        metavar="FILE",
        help="JSON file produced by export_jobs_to_json (optional).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ls = sub.add_parser("list", help="List checkpoints for a job.")
    ls.add_argument("job_id", help="Job ID to inspect.")

    latest = sub.add_parser("latest", help="Show the latest checkpoint for a job.")
    latest.add_argument("job_id", help="Job ID to inspect.")

    ids = sub.add_parser("ids", help="List all job IDs that have checkpoints.")  # noqa: F841

    return parser


def _load_manager(data_path: str | None) -> JobCheckpointManager:
    """Build a manager, optionally pre-populated from a JSON export."""
    manager = JobCheckpointManager()
    if data_path is None:
        return manager
    path = Path(data_path)
    if not path.exists():
        print(f"[warn] data file not found: {path}", file=sys.stderr)
        return manager
    with path.open() as fh:
        records = json.load(fh)
    for rec in records:
        job_id = rec.get("job_id", "")
        for cp_data in rec.get("checkpoints", []):
            manager.add_checkpoint(
                job_id,
                label=cp_data["label"],
                frame=cp_data["frame"],
                note=cp_data.get("note", ""),
            )
    return manager


def run_checkpoints(args: argparse.Namespace) -> int:
    manager = _load_manager(getattr(args, "data", None))

    if args.command == "list":
        cps = manager.get_checkpoints(args.job_id)
        if not cps:
            print(f"No checkpoints for job '{args.job_id}'.")
            return 0
        for cp in cps:
            print(f"  [{cp.frame:>6}] {cp.label}  {cp.timestamp.isoformat()}  {cp.note}")

    elif args.command == "latest":
        cp = manager.latest_checkpoint(args.job_id)
        if cp is None:
            print(f"No checkpoints for job '{args.job_id}'.")
            return 1
        print(f"Latest: [{cp.frame}] {cp.label} @ {cp.timestamp.isoformat()}")
        if cp.note:
            print(f"  Note: {cp.note}")

    elif args.command == "ids":
        ids = manager.all_job_ids()
        if not ids:
            print("No jobs with checkpoints.")
        else:
            for jid in ids:
                print(jid)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_checkpoints(args))


if __name__ == "__main__":  # pragma: no cover
    main()
