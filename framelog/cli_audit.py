"""CLI for querying the job audit log."""

import argparse
import json
import sys
from pathlib import Path

from framelog.job_audit import JobAuditManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-audit",
        description="Query the framelog audit log.",
    )
    parser.add_argument("audit_file", help="Path to JSON audit log file")
    sub = parser.add_subparsers(dest="command", required=True)

    p_job = sub.add_parser("job", help="Show audit entries for a specific job")
    p_job.add_argument("job_id", help="Job ID to query")

    p_actor = sub.add_parser("actor", help="Show audit entries by a specific actor")
    p_actor.add_argument("actor", help="Actor name to query")

    p_action = sub.add_parser("action", help="Show audit entries for a specific action")
    p_action.add_argument("action", help="Action name to query")

    sub.add_parser("all", help="Show all audit entries")
    sub.add_parser("grouped", help="Show entries grouped by job ID")

    return parser


def _load_manager(audit_file: str) -> JobAuditManager:
    path = Path(audit_file)
    if not path.exists():
        print(f"Audit file not found: {audit_file}", file=sys.stderr)
        sys.exit(1)
    with open(path) as fh:
        data = json.load(fh)
    manager = JobAuditManager()
    manager.load_from_dict_list(data)
    return manager


def _print_entries(entries) -> None:
    if not entries:
        print("No entries found.")
        return
    for e in entries:
        detail = f" | {e.detail}" if e.detail else ""
        print(f"[{e.timestamp.isoformat()}] {e.job_id} — {e.action} by {e.actor}{detail}")


def run_audit(args: argparse.Namespace) -> None:
    manager = _load_manager(args.audit_file)

    if args.command == "job":
        _print_entries(manager.entries_for_job(args.job_id))

    elif args.command == "actor":
        _print_entries(manager.entries_by_actor(args.actor))

    elif args.command == "action":
        _print_entries(manager.entries_by_action(args.action))

    elif args.command == "all":
        _print_entries(manager.all_entries())

    elif args.command == "grouped":
        grouped = manager.grouped_by_job()
        if not grouped:
            print("No entries found.")
            return
        for job_id, entries in sorted(grouped.items()):
            print(f"\n{job_id} ({len(entries)} entries):")
            for e in entries:
                detail = f" | {e.detail}" if e.detail else ""
                print(f"  [{e.timestamp.isoformat()}] {e.action} by {e.actor}{detail}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_audit(args)


if __name__ == "__main__":
    main()
