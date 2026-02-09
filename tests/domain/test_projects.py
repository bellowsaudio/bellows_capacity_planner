from datetime import date, datetime, timezone

import pytest

from bcp.domain.projects import (
    InMemoryProjectRepository,
    Project,
    ProjectDeadlineImmutableError,
    ProjectNotFoundError,
    ProjectStatus,
)


def _valid_project(**overrides):
    return Project(
        id=overrides.get("id", "P-001"),
        name=overrides.get("name", "Test Project"),
        status=overrides.get("status", ProjectStatus.BOOKED),
        planned_finished_hours=overrides.get("planned_finished_hours", 10.0),
        contract_start_date=overrides.get("contract_start_date", date(2026, 1, 1)),
        delivery_deadline=overrides.get(
            "delivery_deadline",
            datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc),
        ),
        priority=overrides.get("priority", 1),
        planning_parameters_version_id=overrides.get("planning_parameters_version_id", "PP-001"),
    )


def test_project_can_be_created():
    project = _valid_project()
    assert project.id == "P-001"
    assert project.status is ProjectStatus.BOOKED
    assert project.planning_parameters_version_id == "PP-001"


def test_project_requires_timezone_aware_deadline():
    with pytest.raises(ValueError):
        _valid_project(delivery_deadline=datetime(2026, 1, 31, 12, 0, tzinfo=None))


def test_project_contract_start_must_not_be_after_deadline():
    with pytest.raises(ValueError):
        _valid_project(contract_start_date=date(2026, 2, 1))


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


def test_booked_project_deadline_cannot_change_via_normal_path():
    project = _valid_project(status=ProjectStatus.BOOKED)
    new_deadline = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)

    with pytest.raises(ProjectDeadlineImmutableError):
        project.with_delivery_deadline(new_deadline)


def test_booked_project_deadline_can_change_manually_with_log_entry():
    project = _valid_project(status=ProjectStatus.BOOKED)
    new_deadline = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    changed_at = datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc)

    updated = project.change_delivery_deadline_manual(
        new_deadline, reason="Publisher moved corrections window", changed_at=changed_at
    )

    assert updated.delivery_deadline == new_deadline
    assert updated.delivery_deadline_anchor == project.delivery_deadline
    assert len(updated.deadline_changes) == 1

    ch = updated.deadline_changes[0]
    assert ch.changed_at == changed_at
    assert ch.old_deadline == project.delivery_deadline
    assert ch.new_deadline == new_deadline
    assert ch.reason == "Publisher moved corrections window"


def test_non_booked_project_deadline_can_change_via_normal_path():
    project = _valid_project(status=ProjectStatus.DRAFT, planning_parameters_version_id=None)
    new_deadline = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)

    updated = project.with_delivery_deadline(new_deadline)
    assert updated.delivery_deadline == new_deadline
    # anchor should remain the original creation deadline, not drift
    assert updated.delivery_deadline_anchor == project.delivery_deadline


def test_deadline_change_log_must_form_continuous_chain():
    project = _valid_project(status=ProjectStatus.BOOKED)
    d1 = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    d2 = datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)

    p1 = project.change_delivery_deadline_manual(d1, reason="Reason 1")
    p2 = p1.change_delivery_deadline_manual(d2, reason="Reason 2")

    assert p2.delivery_deadline == d2
    assert len(p2.deadline_changes) == 2
    assert p2.deadline_changes[0].old_deadline == project.delivery_deadline
    assert p2.deadline_changes[0].new_deadline == d1
    assert p2.deadline_changes[1].old_deadline == d1
    assert p2.deadline_changes[1].new_deadline == d2


# --- E3-T2 specific tests ---


def test_draft_project_may_omit_planning_parameters_version_id():
    p = _valid_project(status=ProjectStatus.DRAFT, planning_parameters_version_id=None)
    assert p.planning_parameters_version_id is None


def test_non_draft_project_requires_planning_parameters_version_id():
    with pytest.raises(ValueError, match="required for non-draft projects"):
        _valid_project(status=ProjectStatus.BOOKED, planning_parameters_version_id=None)


def test_planning_parameters_version_id_must_be_non_empty_when_provided():
    with pytest.raises(ValueError, match="must be non-empty"):
        _valid_project(status=ProjectStatus.DRAFT, planning_parameters_version_id="   ")
