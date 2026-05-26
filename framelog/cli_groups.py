"""CLI for managing render job groups.

Usage examples::

    framelog-groups add   --store groups.json --job j1 --group vfx
    framelog-groups remove --store groups.json --job j1 --group vfx
    framelog-groups list   --store groups.json --group vfx
    framelog-groups show   --store groups.json --job j1
    framelog-groups disband --store groups.json --group vfx
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from framelog.job_groups import JobGroupManager


def _load_manager(store: str) -> JobGroupManager:
    p = Path(store)
    if p.exists():
        return JobGroupManager.from_dict(json.loads(p.read_text()))
    return JobGroupManager()


def _save_manager(mgr: JobGroupManager, store: str) -> None:
    Path(store).write_text(json.dumps(mgr.to_dict(), indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framelog-groups",
        description="Manage render job groups.",
    )
    parser.add_argument("--store", default="groups.json", help="Path to group store JSON.")
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Add a job to a group.")
    add_p.add_argument("--job", required=True)
    add_p.add_argument("--group", required=True)

    rem_p = sub.add_parser("remove", help="Remove a job from a group.")
    rem_p.add_argument("--job", required=True)
    rem_p.add_argument("--group", required=True)

    lst_p = sub.add_parser("list", help="List members of a group.")
    lst_p.add_argument("--group", required=True)

    show_p = sub.add_parser("show", help="Show groups a job belongs to.")
    show_p.add_argument("--job", required=True)

    dis_p = sub.add_parser("disband", help="Disband a group entirely.")
    dis_p.add_argument("--group", required=True)

    return parser


def run_groups(args: argparse.Namespace) -> int:
    mgr = _load_manager(args.store)

    if args.command == "add":
        mgr.add_to_group(args.job, args.group)
        _save_manager(mgr, args.store)
        print(f"Added '{args.job}' to group '{args.group}'.")

    elif args.command == "remove":
        mgr.remove_from_group(args.job, args.group)
        _save_manager(mgr, args.store)
        print(f"Removed '{args.job}' from group '{args.group}'.")

    elif args.command == "list":
        members = mgr.members_of(args.group)
        if not members:
            print(f"Group '{args.group}' is empty or does not exist.")
        else:
            for jid in members:
                print(jid)

    elif args.command == "show":
        groups = mgr.groups_for(args.job)
        if not groups:
            print(f"Job '{args.job}' is not in any group.")
        else:
            for g in groups:
                print(g)

    elif args.command == "disband":
        mgr.disband_group(args.group)
        _save_manager(mgr, args.store)
        print(f"Group '{args.group}' disbanded.")

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_groups(build_parser().parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
