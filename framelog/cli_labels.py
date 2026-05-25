"""CLI interface for managing job labels."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from framelog.job_labels import JobLabelManager, LabelConflictError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-labels",
        description="Assign and resolve human-readable labels for render jobs.",
    )
    parser.add_argument(
        "--store",
        default="labels.json",
        help="Path to the JSON file used to persist label mappings (default: labels.json).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    assign_p = sub.add_parser("assign", help="Assign a label to a job.")
    assign_p.add_argument("job_id", help="Job identifier.")
    assign_p.add_argument("label", help="Label string.")

    unassign_p = sub.add_parser("unassign", help="Remove a label mapping.")
    unassign_p.add_argument("label", help="Label to remove.")

    resolve_p = sub.add_parser("resolve", help="Print the job_id for a label.")
    resolve_p.add_argument("label", help="Label to look up.")

    list_p = sub.add_parser("list", help="List all label → job_id mappings.")
    list_p.add_argument("--job", default=None, help="Filter to labels for a specific job.")

    return parser


def _load_manager(store: str) -> JobLabelManager:
    mgr = JobLabelManager()
    path = Path(store)
    if path.exists():
        data: dict = json.loads(path.read_text())
        for label, job_id in data.items():
            mgr.assign(job_id, label)
    return mgr


def _save_manager(mgr: JobLabelManager, store: str) -> None:
    Path(store).write_text(json.dumps(mgr.all_labels(), indent=2))


def run_labels(args: argparse.Namespace) -> int:
    mgr = _load_manager(args.store)

    if args.command == "assign":
        try:
            mgr.assign(args.job_id, args.label)
            _save_manager(mgr, args.store)
            print(f"Assigned '{args.label}' → {args.job_id}")
        except LabelConflictError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    elif args.command == "unassign":
        mgr.unassign(args.label)
        _save_manager(mgr, args.store)
        print(f"Unassigned label '{args.label}'.")

    elif args.command == "resolve":
        job_id = mgr.resolve(args.label)
        if job_id is None:
            print(f"No job found for label '{args.label}'.", file=sys.stderr)
            return 1
        print(job_id)

    elif args.command == "list":
        if args.job:
            labels = mgr.labels_for(args.job)
            for lbl in labels:
                print(lbl)
        else:
            for label, job_id in mgr.all_labels().items():
                print(f"{label}: {job_id}")

    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_labels(args))


if __name__ == "__main__":
    main()
