from datetime import date, datetime, timezone, time

import pytest

from bcp.domain.daily_load import InfeasiblePlanError, compute_daily_load
from bcp.domain.planning_parameters import PlanningParametersVersion
from bcp.domain.projects import Project, ProjectStatus


def _project(
    *,
    pid: str,
    contract_start: date,
    deadline_date: date,
    planned_fh: float,
) -> Project:
    # Use a timezone-aware deadline instant; the window end is deadline_date (Stage-3 rule).
    return Project(
        id=pid,
        name=f"Project {pid}",
        status=ProjectStatus.BOOKED,
        planned_finished_hours=planned_fh,
        contract_start_date=contract_start,
        delivery_deadline=datetime.combine(deadline_date, time(12, 0), tzinfo=timezone.utc),
        priority=1,
        planning_parameters_version_id="PP-001",
    )


def test_daily_load_sums_project_quotas_and_flags_baseline_and_stretch():
    # Project A: 2026-03-01 .. 2026-03-04 (4 days), planned 4 FH => quota 1.0/day
    a = _project(
        pid="P-A",
        contract_start=date(2026, 3, 1),
        deadline_date=date(2026, 3, 4),
        planned_fh=4.0,
    )

    # Project B: 2026-03-03 .. 2026-03-06 (4 days), planned 4 FH => quota 1.0/day
    b = _project(
        pid="P-B",
        contract_start=date(2026, 3, 3),
        deadline_date=date(2026, 3, 6),
        planned_fh=4.0,
    )

    params = PlanningParametersVersion(
        id="PP-1",
        created_at=datetime(2026, 2, 8, 9, 0, tzinfo=timezone.utc),
        baseline_fh_per_day=1.5,
        stretch_fh_per_day=2.5,
    )

    res = compute_daily_load(
        projects=[a, b],
        as_of_date=date(2026, 3, 1),
        ledger_entries=[],
        blocks=[],
        planning_parameters=params,
        closed_days=set(),
    )

    assert res.errors == ()

    # Horizon is 2026-03-01..2026-03-06 inclusive
    assert list(res.daily.keys())[0] == date(2026, 3, 1)
    assert list(res.daily.keys())[-1] == date(2026, 3, 6)

    # Days 1-2: only A => 1.0 (no flags)
    d1 = res.daily[date(2026, 3, 1)]
    assert d1.total_fh == 1.0
    assert d1.exceeds_baseline is False
    assert d1.exceeds_stretch is False

    d2 = res.daily[date(2026, 3, 2)]
    assert d2.total_fh == 1.0
    assert d2.exceeds_baseline is False
    assert d2.exceeds_stretch is False

    # Days 3-4: overlap => 2.0 (exceeds baseline, not stretch)
    d3 = res.daily[date(2026, 3, 3)]
    assert d3.total_fh == 2.0
    assert d3.exceeds_baseline is True
    assert d3.exceeds_stretch is False

    d4 = res.daily[date(2026, 3, 4)]
    assert d4.total_fh == 2.0
    assert d4.exceeds_baseline is True
    assert d4.exceeds_stretch is False

    # Days 5-6: only B => 1.0 (no flags)
    d5 = res.daily[date(2026, 3, 5)]
    assert d5.total_fh == 1.0
    assert d5.exceeds_baseline is False
    assert d5.exceeds_stretch is False

    d6 = res.daily[date(2026, 3, 6)]
    assert d6.total_fh == 1.0
    assert d6.exceeds_baseline is False
    assert d6.exceeds_stretch is False


def test_daily_load_raises_on_infeasible_project():
    # Single-day window, but that only day is closed => 0 recordable days.
    p = _project(
        pid="P-INF",
        contract_start=date(2026, 3, 1),
        deadline_date=date(2026, 3, 1),
        planned_fh=1.0,
    )

    params = PlanningParametersVersion(
        id="PP-1",
        created_at=datetime(2026, 2, 8, 9, 0, tzinfo=timezone.utc),
        baseline_fh_per_day=1.5,
        stretch_fh_per_day=2.5,
    )

    with pytest.raises(InfeasiblePlanError) as exc:
        compute_daily_load(
            projects=[p],
            as_of_date=date(2026, 3, 1),
            ledger_entries=[],
            blocks=[],
            planning_parameters=params,
            closed_days={date(2026, 3, 1)},
        )

    assert "infeasible" in str(exc.value).lower()
    assert "P-INF" in str(exc.value)
