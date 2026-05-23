"""CLI for managing notes on render jobs.

Usage examples
--------------
  framelog-notes add  job-42 --author alice --text "colour grade approved"
  framelog-notes list job-42
  framelog-notes search "OOM"
  framelog-notes clear job-42
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from framelog.job_notes import JobNotesManager

# ---------------------------------------------------------------------------
# Persistence helpers (simple JSON side-car file)
# ---------------------------------------------------------------------------

DEFAULT_STORE = Path("notes_store.json")


def _load_manager(path: Path) -> JobNotesManager:
    mgr = JobNotesManager()
    if path.exists():
        raw = json.loads(path.read_text())
        for job_id, note_list in raw.items():
            for nd in note_list:
                from framelog.job_notes import JobNote  # local import avoids circularity
                mgr._notes.setdefault(job_id, []).append(JobNote.from_dict(nd))
    return mgr


def _save_manager(mgr: JobNotesManager, path: Path) -> None:
    data = {
        job_id: [n.to_dict() for n in notes]
        for job_id, notes in mgr._notes.items()
    }
    path.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="framelog-notes",
        description="Attach and query notes on render jobs.",
    )
    p.add_argument("--store", default=str(DEFAULT_STORE), help="Path to notes JSON store.")
    sub = p.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Add a note to a job.")
    add_p.add_argument("job_id")
    add_p.add_argument("--author", required=True)
    add_p.add_argument("--text", required=True)

    list_p = sub.add_parser("list", help="List notes for a job.")
    list_p.add_argument("job_id")

    search_p = sub.add_parser("search", help="Search notes by keyword.")
    search_p.add_argument("keyword")

    clear_p = sub.add_parser("clear", help="Clear all notes for a job.")
    clear_p.add_argument("job_id")

    return p


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_notes(args: argparse.Namespace) -> None:
    store = Path(args.store)
    mgr = _load_manager(store)

    if args.command == "add":
        note = mgr.add_note(args.job_id, args.author, args.text)
        print(f"Note added to {args.job_id} at {note.created_at.isoformat()}")
        _save_manager(mgr, store)

    elif args.command == "list":
        notes = mgr.get_notes(args.job_id)
        if not notes:
            print(f"No notes for job {args.job_id}.")
        for n in notes:
            print(f"[{n.created_at.isoformat()}] {n.author}: {n.text}")

    elif args.command == "search":
        results = mgr.search_notes(args.keyword)
        if not results:
            print("No matching notes found.")
        for job_id, notes in results.items():
            for n in notes:
                print(f"{job_id} [{n.created_at.isoformat()}] {n.author}: {n.text}")

    elif args.command == "clear":
        count = mgr.clear_notes(args.job_id)
        print(f"Cleared {count} note(s) from {args.job_id}.")
        _save_manager(mgr, store)


def main() -> None:  # pragma: no cover
    run_notes(build_parser().parse_args())


if __name__ == "__main__":  # pragma: no cover
    main()
