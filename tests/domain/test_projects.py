from datetime import date, datetime, timezone

import pytest

from bcp.domain.projects import (
    InMemoryProjectRepository,
    Project,
    ProjectNotFoundError,
    ProjectStatus,
)


def _valid_project(**overrides):
    return Project(
        id=overrides.get("id", "P-001"),
        name=overrides.get("name", "Test Project"),
        status=overrides.get("status", ProjectStatus.BOOKED),
        planned_finished_hours=overrides.get("planned_finished_hours", 10.0),
        contract_start_date=overrides.get(
            "contract_start_date", date(2026, 1, 1)
        ),
        delivery_deadline=overrides.get(
            "delivery_deadline",
            datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc),
        ),
        priority=overrides.get("priority", 1),
    )


def test_project_can_be_created():
    project = _valid_project()
    assert project.id == "P-001"
    assert project.status is ProjectStatus.BOOKED


def test_project_requires_timezone_aware_deadline():
    with pytest.raises(ValueError):
        _valid_project(
            delivery_deadline=datetime(2026, 1, 31, 12, 0)
        )


def test_project_contract_start_must_not_be_after_deadline():
    with pytest.raises(ValueError):
        _valid_project(
            contract_start_date=date(2026, 2, 1)
        )


def test_repository_add_and_get():
    repo = InMemoryProjectRepository()
    project = _valid_project()

    repo.add(project)
    fetched = repo.get(project.id)

    assert fetched is project


def test_repository_get_missing_project_raises():
    repo = InMemoryProjectRepository()

    with pytest.raises(ProjectNotFoundError):
        repo.get("NOPE")
