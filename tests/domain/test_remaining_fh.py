# tests/domain/test_remaining_fh.py

from datetime import date, datetime, timezone

import pytest

from bcp.domain.ledger import LedgerEntry
from bcp.domain.remaining_fh import (
    RemainingFinishedHoursNegativeError,
    compute_remaining_finished_hours,
)
from bcp.domain.projects import Project, ProjectStatus


def _project(**overrides) -> Project:
    return Project(
        id=overrides.get("id", "P-001"),
        name=overrides.get("name", "Test Project"),
        status=overrides.get("status", ProjectStatus.DRAFT),
        planned_finished_hours=overrides.get("planned_finished_hours", 10.0),
        contract_start_date=overrides.get("contract_start_date", date(2026, 1, 1)),
        delivery_deadline=overrides.get(
            "delivery_deadline", datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc)
        ),
        priority=overrides.get("priority", 1),
    )


def _entry(**overrides) -> LedgerEntry:
    return LedgerEntry(
        id=overrides.get("id", "L-001"),
        project_id=overrides.get("project_id", "P-001"),
        finished_hours=overrides.get("finished_hours", 1.0),
        occurred_at=overrides.get(
            "occurred_at", datetime(2026, 2, 8, 9, 0, tzinfo=timezone.utc)
        ),
        note=overrides.get("note", "session"),
    )


def test_remaining_finished_hours_is_planned_minus_recorded():
    p = _project(planned_finished_hours=10.0)
    entries = [
        _entry(id="L-001", project_id=p.id, finished_hours=3.0),
    ]

    remaining = compute_remaining_finished_hours(project=p, ledger_entries=entries)
    assert remaining == 7.0


def test_remaining_finished_hours_can_be_zero():
    p = _project(planned_finished_hours=10.0)
    entries = [
        _entry(id="L-001", project_id=p.id, finished_hours=6.0),
        _entry(id="L-002", project_id=p.id, finished_hours=4.0),
    ]

    remaining = compute_remaining_finished_hours(project=p, ledger_entries=entries)
    assert remaining == 0.0


def test_remaining_finished_hours_negative_raises_explicit_error():
    p = _project(planned_finished_hours=10.0)
    entries = [
        _entry(id="L-001", project_id=p.id, finished_hours=11.0),
    ]

    with pytest.raises(RemainingFinishedHoursNegativeError) as exc:
        compute_remaining_finished_hours(project=p, ledger_entries=entries)

    msg = str(exc.value)
    assert "negative" in msg.lower()
    assert p.id in msg
