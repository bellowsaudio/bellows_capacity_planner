# tests/domain/time/test_moments.py

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from bcp.domain.time.moments import (
    Moment,
    default_contract_deadline,
    effective_window_end_date,
)


def test_default_deadline_winter_vs_us_uk_dst_mismatch():
    """
    Stage-3 acceptance:
    - Winter: 17:00 New York -> 22:00 London
    - US DST on, UK DST not yet: 17:00 New York -> 21:00 London

    We use March 15, 2026 to hit the mismatch window (US DST started, UK not yet).
    """
    winter = default_contract_deadline(date(2026, 1, 15)).to_planning_dt()
    mismatch = default_contract_deadline(date(2026, 3, 15)).to_planning_dt()

    assert winter.hour == 22
    assert mismatch.hour == 21


def test_no_ghost_day_window_end_is_stated_delivery_date():
    """
    Construct a deadline that converts past midnight in London and prove we do NOT
    extend the usable window end-date.
    """
    delivery = date(2026, 1, 15)
    la_tz = ZoneInfo("America/Los_Angeles")

    # 23:30 in LA is the next day morning in London.
    deadline = Moment.from_local(delivery, time(23, 30), la_tz)

    planning_dt = deadline.to_planning_dt()
    assert planning_dt.date() == date(2026, 1, 16)  # sanity check: it did roll over

    assert effective_window_end_date(delivery, deadline) == delivery  # clamp invariant


def test_moment_rejects_naive_datetime():
    with pytest.raises(ValueError):
        Moment.from_aware(datetime(2026, 1, 1, 12, 0))
