from datetime import datetime, timezone

import pytest

from bcp.domain.planning_parameters import (
    InMemoryPlanningParametersRepository,
    PlanningParametersNotFoundError,
    PlanningParametersVersion,
    create_new_version,
    edit_parameters_creates_new_version,
)


def _v(**overrides) -> PlanningParametersVersion:
    return PlanningParametersVersion(
        id=overrides.get("id", "PP-001"),
        created_at=overrides.get(
            "created_at", datetime(2026, 2, 8, 9, 0, tzinfo=timezone.utc)
        ),
        baseline_fh_per_day=overrides.get("baseline_fh_per_day", 2.0),
        stretch_fh_per_day=overrides.get("stretch_fh_per_day", 3.0),
    )


def test_version_requires_timezone_aware_created_at():
    with pytest.raises(ValueError):
        PlanningParametersVersion(
            id="PP-001",
            created_at=datetime(2026, 2, 8, 9, 0),
            baseline_fh_per_day=2.0,
            stretch_fh_per_day=3.0,
        )


def test_stretch_must_be_at_least_baseline():
    with pytest.raises(ValueError):
        _v(baseline_fh_per_day=3.0, stretch_fh_per_day=2.0)


def test_create_new_version_helper_sets_default_timestamp():
    v = create_new_version(version_id="PP-NEW", baseline_fh_per_day=2.0, stretch_fh_per_day=3.0)
    assert v.id == "PP-NEW"
    assert v.created_at.tzinfo is not None


def test_edit_creates_new_version_and_does_not_mutate_prior():
    prior = _v(id="PP-001", baseline_fh_per_day=2.0, stretch_fh_per_day=3.0)
    changed_at = datetime(2026, 2, 8, 10, 0, tzinfo=timezone.utc)

    new = edit_parameters_creates_new_version(
        prior=prior,
        version_id="PP-002",
        baseline_fh_per_day=2.5,
        created_at=changed_at,
    )

    assert prior.id == "PP-001"
    assert prior.baseline_fh_per_day == 2.0  # unchanged

    assert new.id == "PP-002"
    assert new.created_at == changed_at
    assert new.baseline_fh_per_day == 2.5
    assert new.stretch_fh_per_day == 3.0  # carried forward


def test_repository_add_latest_and_list():
    repo = InMemoryPlanningParametersRepository()
    v1 = _v(id="PP-001")
    v2 = _v(id="PP-002", baseline_fh_per_day=2.5)

    repo.add_version(v1)
    repo.add_version(v2)

    assert repo.latest_version() is v2
    assert [v.id for v in repo.list_versions()] == ["PP-001", "PP-002"]
    assert repo.get_version("PP-001") is v1


def test_repository_latest_raises_if_empty():
    repo = InMemoryPlanningParametersRepository()
    with pytest.raises(PlanningParametersNotFoundError):
        repo.latest_version()
