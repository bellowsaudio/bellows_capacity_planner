from datetime import date, datetime, timezone

import pytest

from bcp.domain.blocks import Block
from bcp.domain.ledger import LedgerEntry
from bcp.domain.planning_parameters import PlanningParametersVersion
from bcp.domain.projects import Project, ProjectStatus
from bcp.domain.quota_trace import (
    InfeasibleDailyQuotaWithTraceError,
    compute_daily_quota_with_trace,
)


def _project(
    *,
    contract_start: date,
    deadline_utc: datetime,
    planned_fh: float = 10.0,
) -> Project:
    return Project(
        id="p1",
        name="Test Project",
        status=ProjectStatus.DRAFT,
        planned_finished_hours=planned_fh,
        contract_start_date=contract_start,
        delivery_deadline=deadline_utc,
        priority=1,
    )


def _entry(*, project_id: str, fh: float) -> LedgerEntry:
    return LedgerEntry(
        id="L-001",
        project_id=project_id,
        finished_hours=fh,
        occurred_at=datetime(2026, 2, 8, 9, 0, tzinfo=timezone.utc),
        note="session",
    )


def _params() -> PlanningParametersVersion:
    return PlanningParametersVersion(
        id="PP-001",
        created_at=datetime(2026, 2, 1, 9, 0, tzinfo=timezone.utc),
        baseline_fh_per_day=2.0,
        stretch_fh_per_day=3.0,
    )


def test_trace_matches_hand_calculation_for_quota():
    # Window 10..12 inclusive => 3 candidate days
    # Away on 11 removes 1 => remaining_recordable_days = 2
    # planned=10, recorded=3 => remaining_fh=7
    # quota = 7 / 2 = 3.5
    p = _project(
        contract_start=date(2026, 3, 10),
        deadline_utc=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
        planned_fh=10.0,
    )
    away = Block.create("AWAY_FROM_STUDIO", date(2026, 3, 11), date(2026, 3, 11))
    entries = [_entry(project_id=p.id, fh=3.0)]

    res = compute_daily_quota_with_trace(
        project=p,
        as_of_date=date(2026, 3, 10),
        blocks=[away],
        ledger_entries=entries,
        parameters_version=_params(),
        closed_days=set(),
        day_overrides=[],
    )

    assert res.quota_fh_per_day == 3.5

    t = res.trace
    assert t.project_id == p.id
    assert t.as_of_date == date(2026, 3, 10)

    assert t.remaining_fh == 7.0
    assert t.remaining_recordable_days == 2

    assert date(2026, 3, 11) in t.excluded_away
    assert len(t.excluded_closed) == 0
    assert len(t.excluded_no_recording_override) == 0

    assert t.parameter_version_id == "PP-001"
    assert t.baseline_fh_per_day == 2.0
    assert t.stretch_fh_per_day == 3.0

    # Deadline moment is present and should be timezone-aware internally
    assert t.deadline_moment is not None

    # Output is included inside the trace too
    assert t.quota_fh_per_day == 3.5


def test_infeasible_quota_raises_and_carries_trace():
    # Single-day window, but that day is away => remaining_recordable_days = 0
    # remaining_fh > 0 => infeasible
    p = _project(
        contract_start=date(2026, 3, 10),
        deadline_utc=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
        planned_fh=1.0,
    )
    away = Block.create("AWAY_FROM_STUDIO", date(2026, 3, 10), date(2026, 3, 10))

    with pytest.raises(InfeasibleDailyQuotaWithTraceError) as exc:
        compute_daily_quota_with_trace(
            project=p,
            as_of_date=date(2026, 3, 10),
            blocks=[away],
            ledger_entries=[],
            parameters_version=_params(),
            closed_days=set(),
            day_overrides=[],
        )

    err = exc.value
    assert "infeasible" in str(err).lower()

    trace = err.trace
    assert trace.project_id == p.id
    assert trace.remaining_fh == 1.0
    assert trace.remaining_recordable_days == 0
    assert date(2026, 3, 10) in trace.excluded_away
    assert trace.parameter_version_id == "PP-001"
    assert trace.deadline_moment is not None
