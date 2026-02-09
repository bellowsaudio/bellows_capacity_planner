from datetime import date, datetime, timezone

import pytest

from bcp.domain.day_overrides import (
    DayOverride,
    DayOverrideType,
    DuplicateDayOverrideForDayError,
    InMemoryDayOverrideRepository,
    no_recording_days_for_project,
)


def test_day_override_requires_timezone_aware_set_at():
    with pytest.raises(ValueError, match="set_at must be timezone-aware"):
        DayOverride(
            id="O-1",
            project_id="P-1",
            day=date(2026, 3, 10),
            override_type=DayOverrideType.NO_RECORDING,
            set_at=datetime(2026, 3, 10, 9, 0),  # naive
        )


def test_repo_rejects_conflicting_duplicate_for_same_project_day_type():
    repo = InMemoryDayOverrideRepository()

    o1 = DayOverride(
        id="O-1",
        project_id="P-1",
        day=date(2026, 3, 10),
        override_type=DayOverrideType.NO_RECORDING,
        set_at=datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
        note="First",
    )
    repo.add(o1)

    o2 = DayOverride(
        id="O-2",
        project_id="P-1",
        day=date(2026, 3, 10),
        override_type=DayOverrideType.NO_RECORDING,
        set_at=datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc),
        note="Second attempt",
    )

    with pytest.raises(DuplicateDayOverrideForDayError):
        repo.add(o2)


def test_no_recording_days_for_project_filters_correctly():
    o1 = DayOverride(
        id="O-1",
        project_id="P-1",
        day=date(2026, 3, 10),
        override_type=DayOverrideType.NO_RECORDING,
        set_at=datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
    )
    o2 = DayOverride(
        id="O-2",
        project_id="P-2",
        day=date(2026, 3, 10),
        override_type=DayOverrideType.NO_RECORDING,
        set_at=datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
    )

    assert no_recording_days_for_project([o1, o2], project_id="P-1") == {date(2026, 3, 10)}
