"""CLI entry point for evaluating alert rules against a JSON job export."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from framelog.job_status import RenderJob, RenderStatus
from framelog.job_alerts import AlertRule, JobAlertManager
from framelog.alert_channel import InMemoryChannel


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="framelog-alerts",
        description="Evaluate alert rules against a job export and report matches.",
    )
    p.add_argument("jobs_json", help="Path to JSON file produced by export_jobs_to_json.")
    p.add_argument(
        "--trigger",
        choices=[s.value for s in RenderStatus],
        action="append",
        dest="triggers",
        default=[],
        metavar="STATUS",
        help="Status value that triggers an alert (repeatable).",
    )
    p.add_argument(
        "--server",
        default=None,
        metavar="SERVER_ID",
        help="Restrict alerts to a specific server.",
    )
    p.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return p


def _load_jobs(path: str) -> List[RenderJob]:
    with open(path, encoding="utf-8") as fh:
        records = json.load(fh)
    jobs: List[RenderJob] = []
    for r in records:
        job = RenderJob(
            job_id=r["job_id"],
            scene_file=r.get("scene_file", ""),
            frame_range=tuple(r.get("frame_range", [1, 1])),
            server_id=r.get("server_id"),
        )
        job.status = RenderStatus(r["status"])
        job.error_message = r.get("error_message")
        jobs.append(job)
    return jobs


def run_alerts(args: argparse.Namespace) -> int:
    jobs = _load_jobs(args.jobs_json)
    triggers = args.triggers or [RenderStatus.FAILED.value]
    channel = InMemoryChannel()
    manager = JobAlertManager()

    for i, trigger in enumerate(triggers):
        rule = AlertRule(
            name=f"cli-rule-{i}",
            status_trigger=RenderStatus(trigger),
            server_filter=args.server,
        )
        manager.add_rule(rule)

    for job in jobs:
        events = manager.evaluate(job)
        for ev in events:
            channel.send(ev)

    fired = channel.events()
    if args.output == "json":
        print(json.dumps([e.to_dict() for e in fired], indent=2))
    else:
        if not fired:
            print("No alerts triggered.")
        for ev in fired:
            msg = f"ALERT  rule={ev.rule_name}  job={ev.job_id}  status={ev.status.value}"
            if ev.server_id:
                msg += f"  server={ev.server_id}"
            if ev.message:
                msg += f"  error={ev.message!r}"
            print(msg)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_alerts(args))


if __name__ == "__main__":  # pragma: no cover
    main()
