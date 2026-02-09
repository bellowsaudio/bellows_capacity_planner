# tests/domain/test_remaining_days.py

from datetime import date, datetime, timezone

from bcp.domain.blocks import Block
from bcp.domain.remaining_days import compute_remaining_recordable_days
from bcp.domain.projects import Project, ProjectStatus


def _project(
    *,
    contract_start: date,
    deadline_utc: datetime,
) -> Project:
    return Project(
        id="p1",
        name="Test Project",
        status=ProjectStatus.DRAFT,
        planned_finished_hours=10.0,
        contract_start_date=contract_start,
        delivery_deadline=deadline_utc,
        priority=1,
    )


def test_single_day_window_counts_as_one_when_recordable():
    # contract_start_date == delivery_deadline.date() => 1-day inclusive window
    p = _project(
        contract_start=date(2026, 3, 10),
        deadline_utc=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
    )

    res = compute_remaining_recordable_days(
        project=p,
        as_of_date=date(2026, 3, 10),
        blocks=[],
        closed_days=set(),
    )

    assert res.remaining_recordable_days == 1
    assert res.window.start_date == date(2026, 3, 10)
    assert res.window.end_date == date(2026, 3, 10)


def test_away_removes_exactly_one_day():
    p = _project(
        contract_start=date(2026, 3, 10),
        deadline_utc=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
    )

    away = Block.create("AWAY_FROM_STUDIO", date(2026, 3, 11), date(2026, 3, 11))

    res = compute_remaining_recordable_days(
        project=p,
        as_of_date=date(2026, 3, 10),
        blocks=[away],
        closed_days=set(),
    )

    # Window is 10..12 inclusive => 3 days, minus 1 away => 2
    assert res.remaining_recordable_days == 2
    assert date(2026, 3, 11) in res.excluded_away


def test_closed_day_removes_exactly_one_day():
    p = _project(
        contract_start=date(2026, 3, 10),
        deadline_utc=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
    )

    res = compute_remaining_recordable_days(
        project=p,
        as_of_date=date(2026, 3, 10),
        blocks=[],
        closed_days={date(2026, 3, 11)},
    )

    assert res.remaining_recordable_days == 2
    assert date(2026, 3, 11) in res.excluded_closed


def test_as_of_date_clips_start_but_does_not_move_endpoints():
    p = _project(
        contract_start=date(2026, 3, 1),
        deadline_utc=datetime(2026, 3, 31, 12, 0, tzinfo=timezone.utc),
    )

    res = compute_remaining_recordable_days(
        project=p,
        as_of_date=date(2026, 3, 10),
        blocks=[],
        closed_days=set(),
    )

    # remaining window evaluated is 10..31 inclusive => 22 days
    assert res.remaining_recordable_days == 22
    assert res.evaluated_start_date == date(2026, 3, 10)
    assert res.evaluated_end_date == date(2026, 3, 31)

    # Original window endpoints remain canonical
    assert res.window.start_date == date(2026, 3, 1)
    assert res.window.end_date == date(2026, 3, 31)


def test_final_day_excluded_if_covered_by_buffer_like_block():
    p = _project(
        contract_start=date(2026, 3, 10),
        deadline_utc=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
    )

    # final day == 2026-03-12
    sick_buffer = Block.create("SICK_BUFFER", date(2026, 3, 12), date(2026, 3, 12))

    res = compute_remaining_recordable_days(
        project=p,
        as_of_date=date(2026, 3, 10),
        blocks=[sick_buffer],
        closed_days=set(),
    )

    # Window 10..12 inclusive => 3 days, but final day excluded => 2
    assert res.remaining_recordable_days == 2
    assert date(2026, 3, 12) in res.excluded_nonrecordable_final_day
