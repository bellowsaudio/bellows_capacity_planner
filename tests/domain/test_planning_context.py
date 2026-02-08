from datetime import datetime, timezone

import pytest

from bcp.domain.planning_context import (
    InMemoryPlanningContextRepository,
    PlanningContextNotFoundError,
    PlanningContextVersionPointer,
    set_active_planning_parameters,
)


def _p(**overrides) -> PlanningContextVersionPointer:
    return PlanningContextVersionPointer(
        id=overrides.get("id", "PC-001"),
        active_version_id=overrides.get("active_version_id", "PP-001"),
        set_at=overrides.get(
            "set_at", datetime(2026, 2, 8, 9, 0, tzinfo=timezone.utc)
        ),
        reason=overrides.get("reason", "initial"),
    )


def test_pointer_requires_timezone_aware_set_at():
    with pytest.raises(ValueError):
        PlanningContextVersionPointer(
            id="PC-001",
            active_version_id="PP-001",
            set_at=datetime(2026, 2, 8, 9, 0),
        )


def test_set_active_helper_sets_default_timestamp():
    p = set_active_planning_parameters(pointer_id="PC-NEW", active_version_id="PP-002")
    assert p.id == "PC-NEW"
    assert p.active_version_id == "PP-002"
    assert p.set_at.tzinfo is not None


def test_repository_add_latest_and_list():
    repo = InMemoryPlanningContextRepository()
    p1 = _p(id="PC-001", active_version_id="PP-001")
    p2 = _p(id="PC-002", active_version_id="PP-002")

    repo.add_pointer(p1)
    repo.add_pointer(p2)

    assert repo.latest_pointer() is p2
    assert [p.id for p in repo.list_pointers()] == ["PC-001", "PC-002"]
    assert repo.get_pointer("PC-001") is p1


def test_repository_latest_raises_if_empty():
    repo = InMemoryPlanningContextRepository()
    with pytest.raises(PlanningContextNotFoundError):
        repo.latest_pointer()
