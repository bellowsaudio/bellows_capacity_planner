from datetime import datetime, timezone

import pytest

from bcp.domain.ledger import (
    InMemoryLedgerRepository,
    LedgerAppendOnlyError,
    LedgerEntry,
    LedgerEntryNotFoundError,
    total_finished_hours_for_project,
    totals_by_project,
)



def _entry(**overrides) -> LedgerEntry:
    return LedgerEntry(
        id=overrides.get("id", "L-001"),
        project_id=overrides.get("project_id", "P-001"),
        finished_hours=overrides.get("finished_hours", 1.5),
        occurred_at=overrides.get(
            "occurred_at", datetime(2026, 2, 8, 9, 0, tzinfo=timezone.utc)
        ),
        note=overrides.get("note", "session"),
    )


def test_entry_requires_timezone_aware_occurred_at():
    with pytest.raises(ValueError):
        _entry(occurred_at=datetime(2026, 2, 8, 9, 0))


def test_entry_finished_hours_must_be_nonzero():
    with pytest.raises(ValueError):
        _entry(finished_hours=0)


def test_negative_finished_hours_allowed_for_compensating_entries():
    e = _entry(finished_hours=-0.5)
    assert e.finished_hours == -0.5


def test_repo_add_get_and_list_order():
    repo = InMemoryLedgerRepository()
    e1 = _entry(id="L-001", finished_hours=1.0)
    e2 = _entry(id="L-002", finished_hours=2.0)

    repo.add(e1)
    repo.add(e2)

    assert repo.get("L-001") is e1
    assert [e.id for e in repo.list_entries()] == ["L-001", "L-002"]


def test_repo_list_can_filter_by_project():
    repo = InMemoryLedgerRepository()
    repo.add(_entry(id="L-001", project_id="P-001"))
    repo.add(_entry(id="L-002", project_id="P-002"))
    repo.add(_entry(id="L-003", project_id="P-001"))

    ids = [e.id for e in repo.list_entries(project_id="P-001")]
    assert ids == ["L-001", "L-003"]


def test_repo_get_missing_raises():
    repo = InMemoryLedgerRepository()
    with pytest.raises(LedgerEntryNotFoundError):
        repo.get("NOPE")


def test_repo_is_append_only_update_and_delete_raise():
    repo = InMemoryLedgerRepository()
    repo.add(_entry())

    with pytest.raises(LedgerAppendOnlyError):
        repo.update(_entry(note="attempted edit"))

    with pytest.raises(LedgerAppendOnlyError):
        repo.delete("L-001")
def test_total_finished_hours_for_project_sums_only_that_project():
    entries = [
        _entry(id="L-001", project_id="P-001", finished_hours=1.0),
        _entry(id="L-002", project_id="P-002", finished_hours=2.0),
        _entry(id="L-003", project_id="P-001", finished_hours=0.5),
    ]

    assert total_finished_hours_for_project(entries, project_id="P-001") == 1.5
    assert total_finished_hours_for_project(entries, project_id="P-002") == 2.0


def test_total_finished_hours_for_project_includes_negative_entries():
    entries = [
        _entry(id="L-001", project_id="P-001", finished_hours=2.0),
        _entry(id="L-002", project_id="P-001", finished_hours=-0.5),
    ]

    assert total_finished_hours_for_project(entries, project_id="P-001") == 1.5


def test_total_finished_hours_for_project_empty_is_zero():
    assert total_finished_hours_for_project([], project_id="P-001") == 0.0


def test_totals_by_project_groups_and_sums():
    entries = [
        _entry(id="L-001", project_id="P-001", finished_hours=1.0),
        _entry(id="L-002", project_id="P-002", finished_hours=2.0),
        _entry(id="L-003", project_id="P-001", finished_hours=0.5),
        _entry(id="L-004", project_id="P-002", finished_hours=-0.25),
    ]

    totals = totals_by_project(entries)
    assert totals["P-001"] == 1.5
    assert totals["P-002"] == 1.75


def test_totals_by_project_empty_is_empty_dict():
    assert totals_by_project([]) == {}
