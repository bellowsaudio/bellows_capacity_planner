from datetime import date, datetime, timezone

import pytest

from bcp.domain.day_closures import (
    DayClosure,
    DuplicateDayClosureForDateError,
    InMemoryDayClosureRepository,
    closed_days_from_closures,
)
from bcp.domain.remaining_days import compute_remaining_recordable_days
from bcp.domain.projects import Project, ProjectStatus


def _project(*, contract_start: date, deadline_utc: datetime) -> Project:
    return Project(
        id="p1",
        name="Test Project",
        status=ProjectStatus.DRAFT,
        planned_finished_hours=10.0,
        contract_start_date=contract_start,
        delivery_deadline=deadline_utc,
        priority=1,
    )


def test_day_closure_requires_timezone_aware_closed_at():
    with pytest.raises(ValueError, match="closed_at must be timezone-aware"):
        DayClosure(
            id="c1",
            day=date(2026, 3, 10),
            closed_at=datetime(2026, 3, 10, 18, 0),  # naive
            note="",
        )


def test_repo_rejects_second_closure_for_same_day():
    repo = InMemoryDayClosureRepository()

    c1 = DayClosure(
        id="c1",
        day=date(2026, 3, 10),
        closed_at=datetime(2026, 3, 10, 18, 0, tzinfo=timezone.utc),
        note="first",
    )
    repo.add(c1)

    c2 = DayClosure(
        id="c2",
        day=date(2026, 3, 10),
        closed_at=datetime(2026, 3, 10, 19, 0, tzinfo=timezone.utc),
        note="second attempt",
    )

    with pytest.raises(DuplicateDayClosureForDateError):
        repo.add(c2)


def test_closed_days_read_model_derives_dates():
    closures = [
        DayClosure(
            id="c1",
            day=date(2026, 3, 10),
            closed_at=datetime(2026, 3, 10, 18, 0, tzinfo=timezone.utc),
        ),
        DayClosure(
            id="c2",
            day=date(2026, 3, 11),
            closed_at=datetime(2026, 3, 11, 18, 0, tzinfo=timezone.utc),
        ),
    ]
    assert closed_days_from_closures(closures) == {date(2026, 3, 10), date(2026, 3, 11)}


def test_closing_today_removes_it_from_remaining_recordable_days():
    """
    E2-T3 acceptance: Closing a day reduces remaining recordable days.

    This matters specifically when as_of_date == that day; otherwise the day would
    already be in the past and clipped out by evaluated_start.
    """
    p = _project(
        contract_start=date(2026, 3, 10),
        deadline_utc=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
    )

    closure = DayClosure(
        id="c1",
        day=date(2026, 3, 10),
        closed_at=datetime(2026, 3, 10, 18, 0, tzinfo=timezone.utc),
        note="Day closed",
    )

    closed_days = closed_days_from_closures([closure])

    res = compute_remaining_recordable_days(
        project=p,
        as_of_date=date(2026, 3, 10),
        blocks=[],
        closed_days=closed_days,
    )

    # Window 10..12 inclusive => 3 days; closed(10) removes 1 => 2.
    assert res.remaining_recordable_days == 2
    assert date(2026, 3, 10) in res.excluded_closed
