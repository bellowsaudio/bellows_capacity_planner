from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from bcp.domain.blocks import Block
from bcp.domain.daily_load import InfeasiblePlanError, compute_daily_load
from bcp.domain.ledger import LedgerEntry
from bcp.domain.planning_parameters import PlanningParametersVersion
from bcp.domain.projects import Project, ProjectStatus


def _dt(s: str) -> datetime:
    """
    Parse an ISO-8601 timezone-aware datetime string.
    """
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware")
    return dt


def _project(
    *,
    id: str,
    name: str,
    status: ProjectStatus,
    planned_finished_hours: float,
    contract_start_date: date,
    delivery_deadline_iso: str,
    priority: int,
    planning_parameters_version_id: str | None,
) -> Project:
    return Project(
        id=id,
        name=name,
        status=status,
        planned_finished_hours=planned_finished_hours,
        contract_start_date=contract_start_date,
        delivery_deadline=_dt(delivery_deadline_iso),
        priority=priority,
        planning_parameters_version_id=planning_parameters_version_id,
    )


def _entry(
    *,
    id: str,
    project_id: str,
    finished_hours: float,
    occurred_at_iso: str,
    note: str,
) -> LedgerEntry:
    return LedgerEntry(
        id=id,
        project_id=project_id,
        finished_hours=finished_hours,
        occurred_at=_dt(occurred_at_iso),
        note=note,
    )


def test_booking_safety_scenario_v1_current_vs_with_candidate():
    # --- normalized dataset (real-life) ---
    as_of = date(2026, 2, 9)

    planning_parameters = PlanningParametersVersion(
        id="PP-REAL-001",
        created_at=datetime(2026, 2, 9, 0, 0, tzinfo=timezone.utc),
        baseline_fh_per_day=1.2,
        stretch_fh_per_day=2.2,
    )

    # Booked projects
    a = _project(
        id="A",
        name="MDP",
        status=ProjectStatus.BOOKED,
        planned_finished_hours=13.2,
        contract_start_date=date(2026, 2, 10),
        delivery_deadline_iso="2026-03-25T22:00:00+00:00",
        priority=1,
        planning_parameters_version_id="PP-REAL-001",
    )
    b = _project(
        id="B",
        name="DWAD",
        status=ProjectStatus.BOOKED,
        planned_finished_hours=5.0,
        contract_start_date=date(2026, 2, 17),
        delivery_deadline_iso="2026-02-25T22:00:00+00:00",
        priority=1,
        planning_parameters_version_id="PP-REAL-001",
    )
    c = _project(
        id="C",
        name="TBB",
        status=ProjectStatus.BOOKED,
        planned_finished_hours=10.0,
        contract_start_date=date(2026, 2, 5),
        delivery_deadline_iso="2026-02-24T22:00:00+00:00",
        priority=1,
        planning_parameters_version_id="PP-REAL-001",
    )

    # Candidate project (draft)
    d = _project(
        id="D",
        name="Resil",
        status=ProjectStatus.DRAFT,
        planned_finished_hours=10.0,
        contract_start_date=as_of,
        delivery_deadline_iso="2026-03-15T22:00:00+00:00",
        priority=2,
        planning_parameters_version_id=None,
    )

    # Ledger: only A has any recorded FH so far
    ledger_entries = [
        _entry(
            id="L1",
            project_id="A",
            finished_hours=0.5,
            occurred_at_iso="2026-02-08T09:00:00+00:00",
            note="session",
        )
    ]

    # Blocks: away days + publisher corrections window (not necessarily binding any final day here,
    # but included to keep scenario realistic)
    blocks = [
        Block.create("AWAY_FROM_STUDIO", date(2026, 2, 14), date(2026, 2, 16)),
        Block.create("PUBLISHER_CORRECTIONS_WINDOW", date(2026, 3, 1), date(2026, 3, 1)),
    ]

    closed_days: set[date] = set()

    # --- run: current bookings ---
    current = compute_daily_load(
        projects=[a, b, c],
        as_of_date=as_of,
        ledger_entries=ledger_entries,
        blocks=blocks,
        planning_parameters=planning_parameters,
        closed_days=closed_days,
    )

    # Basic integrity: horizon includes as_of date and is non-empty
    assert as_of in current.daily
    assert len(current.daily) > 0

    # Away days should have zero total load (recording not allowed at all)
    assert current.daily[date(2026, 2, 14)].total_fh == 0.0
    assert current.daily[date(2026, 2, 15)].total_fh == 0.0
    assert current.daily[date(2026, 2, 16)].total_fh == 0.0

    # No non-infeasible errors expected from this dataset
    assert current.errors == ()

    # --- run: add candidate booking ---
    with_candidate = compute_daily_load(
        projects=[a, b, c, d],
        as_of_date=as_of,
        ledger_entries=ledger_entries,
        blocks=blocks,
        planning_parameters=planning_parameters,
        closed_days=closed_days,
    )

    assert as_of in with_candidate.daily
    assert with_candidate.errors == ()

    # Adding candidate should increase load on at least one day that is recordable for D.
    # (We don't assert exact numeric values here; we assert monotonicity somewhere in horizon.)
    increased_somewhere = False
    for day, load in current.daily.items():
        if day in with_candidate.daily:
            if with_candidate.daily[day].total_fh > load.total_fh:
                increased_somewhere = True
                break

    assert increased_somewhere is True


def test_booking_safety_scenario_v1_raises_infeasible_plan_if_candidate_makes_days_zero():
    """
    Guardrail: if you ever adjust the dataset (more away/closures/etc.) such that a project has
    remaining FH but zero recordable days, this should raise explicitly (E10-T1 behavior).
    """
    as_of = date(2026, 2, 9)
    planning_parameters = PlanningParametersVersion(
        id="PP-REAL-001",
        created_at=datetime(2026, 2, 9, 0, 0, tzinfo=timezone.utc),
        baseline_fh_per_day=1.2,
        stretch_fh_per_day=2.2,
    )

    d = Project(
        id="D",
        name="Resil",
        status=ProjectStatus.DRAFT,
        planned_finished_hours=10.0,
        contract_start_date=as_of,
        delivery_deadline=_dt("2026-02-09T22:00:00+00:00"),
        priority=2,
        planning_parameters_version_id=None,
    )

    # Make the only day recordable impossible via AWAY
    blocks = [Block.create("AWAY_FROM_STUDIO", as_of, as_of)]

    with pytest.raises(InfeasiblePlanError) as exc:
        compute_daily_load(
            projects=[d],
            as_of_date=as_of,
            ledger_entries=[],
            blocks=blocks,
            planning_parameters=planning_parameters,
            closed_days=set(),
        )

    assert "infeasible" in str(exc.value).lower()
