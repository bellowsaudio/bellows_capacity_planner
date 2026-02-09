from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable, Sequence

from bcp.domain.blocks import Block
from bcp.domain.daily_load import InfeasiblePlanError, compute_daily_load
from bcp.domain.ledger import LedgerEntry
from bcp.domain.planning_parameters import PlanningParametersVersion
from bcp.domain.projects import Project, ProjectStatus


def _dt(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError(f"Datetime must be timezone-aware: {s}")
    return dt


@dataclass(frozen=True, slots=True)
class ScenarioInputs:
    as_of_date: date
    planning_parameters: PlanningParametersVersion
    projects: Sequence[Project]
    candidate_project: Project
    ledger_entries: Sequence[LedgerEntry]
    blocks: Sequence[Block]
    closed_days: set[date]


def booking_safety_scenario_v1() -> ScenarioInputs:
    """
    Canonical scenario runner input matching tests/integration/test_booking_safety_scenario_v1.py.

    This is intentionally hard-coded for now (Stage-5 verification harness):
    - easy to run
    - stable
    - auditable
    """
    as_of = date(2026, 2, 9)

    planning_parameters = PlanningParametersVersion(
        id="PP-REAL-001",
        created_at=datetime(2026, 2, 9, 0, 0, tzinfo=timezone.utc),
        baseline_fh_per_day=1.2,
        stretch_fh_per_day=2.2,
    )

    a = Project(
        id="A",
        name="MDP",
        status=ProjectStatus.BOOKED,
        planned_finished_hours=13.2,
        contract_start_date=date(2026, 2, 10),
        delivery_deadline=_dt("2026-03-25T22:00:00+00:00"),
        priority=1,
        planning_parameters_version_id="PP-REAL-001",
    )

    b = Project(
        id="B",
        name="DWAD",
        status=ProjectStatus.BOOKED,
        planned_finished_hours=5.0,
        contract_start_date=date(2026, 2, 17),
        delivery_deadline=_dt("2026-02-25T22:00:00+00:00"),
        priority=1,
        planning_parameters_version_id="PP-REAL-001",
    )

    c = Project(
        id="C",
        name="TBB",
        status=ProjectStatus.BOOKED,
        planned_finished_hours=10.0,
        contract_start_date=date(2026, 2, 5),
        delivery_deadline=_dt("2026-02-24T22:00:00+00:00"),
        priority=1,
        planning_parameters_version_id="PP-REAL-001",
    )

    candidate = Project(
        id="D",
        name="Resil",
        status=ProjectStatus.DRAFT,
        planned_finished_hours=10.0,
        contract_start_date=as_of,
        delivery_deadline=_dt("2026-03-15T22:00:00+00:00"),
        priority=2,
        planning_parameters_version_id=None,
    )

    ledger_entries = [
        LedgerEntry(
            id="L1",
            project_id="A",
            finished_hours=0.5,
            occurred_at=_dt("2026-02-08T09:00:00+00:00"),
            note="session",
        )
    ]

    blocks = [
        Block.create("AWAY_FROM_STUDIO", date(2026, 2, 14), date(2026, 2, 16)),
        Block.create("PUBLISHER_CORRECTIONS_WINDOW", date(2026, 3, 1), date(2026, 3, 1)),
    ]

    return ScenarioInputs(
        as_of_date=as_of,
        planning_parameters=planning_parameters,
        projects=[a, b, c],
        candidate_project=candidate,
        ledger_entries=ledger_entries,
        blocks=blocks,
        closed_days=set(),
    )


def _format_flag(baseline: bool, stretch: bool) -> str:
    if stretch:
        return "EXCEEDS_STRETCH"
    if baseline:
        return "EXCEEDS_BASELINE"
    return "OK"


def run_booking_safety_v1(*, include_candidate: bool) -> int:
    s = booking_safety_scenario_v1()
    projects = list(s.projects)
    if include_candidate:
        projects.append(s.candidate_project)

    try:
        res = compute_daily_load(
            projects=projects,
            as_of_date=s.as_of_date,
            ledger_entries=s.ledger_entries,
            blocks=s.blocks,
            planning_parameters=s.planning_parameters,
            closed_days=s.closed_days,
        )
    except InfeasiblePlanError as e:
        print(str(e))
        return 2

    if res.errors:
        print("Non-fatal computation errors detected:")
        for err in res.errors:
            print(f"- {err.project_id}: {err.error_type}: {err.message}")
        # Continue printing daily load; errors are explicit and inspectable.

    # Stable day order
    for d in sorted(res.daily.keys()):
        load = res.daily[d]
        flag = _format_flag(load.exceeds_baseline, load.exceeds_stretch)
        print(f"{d.isoformat()}  total_fh={load.total_fh:.4f}  {flag}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bcp",
        description="Bellows Capacity Planner — read-only scenario runner",
    )
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser(
        "booking-safety-v1",
        help="Run the booking safety scenario v1 (real dataset fixture)",
    )
    s.add_argument(
        "--include-candidate",
        action="store_true",
        help="Include the candidate project in the daily load computation",
    )

    return p


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "booking-safety-v1":
        return run_booking_safety_v1(include_candidate=bool(args.include_candidate))

    raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
