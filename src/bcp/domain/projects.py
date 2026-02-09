from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from enum import Enum
from typing import Dict, Optional, Tuple


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    BOOKED = "booked"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"


@dataclass(frozen=True)
class DeadlineChange:
    changed_at: datetime
    old_deadline: datetime
    new_deadline: datetime
    reason: str

    def __post_init__(self) -> None:
        if self.changed_at.tzinfo is None:
            raise ValueError("changed_at must be timezone-aware")

        if self.old_deadline.tzinfo is None:
            raise ValueError("old_deadline must be timezone-aware")

        if self.new_deadline.tzinfo is None:
            raise ValueError("new_deadline must be timezone-aware")

        if not self.reason.strip():
            raise ValueError("reason must be non-empty")


class ProjectDeadlineImmutableError(ValueError):
    """Raised when attempting to change a BOOKED project's deadline via a non-manual path."""


@dataclass(frozen=True)
class Project:
    """
    Canonical Project entity.

    A Project:
    - defines commercial intent (scope, priority, deadlines)
    - does NOT own time directly
    - is referenced by blocks and ledger entries

    E3-T2:
    - planning_parameters_version_id binds the project to the parameters version used
      for planning (baseline/stretch assumptions) at booking time.
    """

    id: str
    name: str
    status: ProjectStatus
    planned_finished_hours: float
    contract_start_date: date
    delivery_deadline: datetime
    priority: int

    # E3-T2: bind project to planning parameters version (required once not DRAFT).
    planning_parameters_version_id: Optional[str] = None

    # --- E6-T2: Deadline immutability / audit trail ---
    # Anchor is set on first creation and preserved across copies.
    delivery_deadline_anchor: Optional[datetime] = None
    deadline_changes: Tuple[DeadlineChange, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Project name must be non-empty")

        if self.planned_finished_hours < 0:
            raise ValueError("planned_finished_hours must be >= 0")

        if self.delivery_deadline.tzinfo is None:
            raise ValueError("delivery_deadline must be timezone-aware")

        if self.contract_start_date > self.delivery_deadline.date():
            raise ValueError("contract_start_date cannot be after delivery_deadline")

        # E3-T2 validation: enforce binding once the project is not a draft.
        if self.planning_parameters_version_id is not None:
            if not self.planning_parameters_version_id.strip():
                raise ValueError("planning_parameters_version_id must be non-empty when provided")

        if self.status is not ProjectStatus.DRAFT:
            if self.planning_parameters_version_id is None:
                raise ValueError(
                    "planning_parameters_version_id is required for non-draft projects"
                )

        # Initialize anchor on first creation (and preserve on dataclasses.replace copies).
        if self.delivery_deadline_anchor is None:
            object.__setattr__(self, "delivery_deadline_anchor", self.delivery_deadline)
        else:
            if self.delivery_deadline_anchor.tzinfo is None:
                raise ValueError("delivery_deadline_anchor must be timezone-aware")

        self._validate_deadline_changes()

    def _validate_deadline_changes(self) -> None:
        anchor = self.delivery_deadline_anchor
        assert anchor is not None  # set in __post_init__

        # If there are changes, they must form a consistent chain.
        if self.deadline_changes:
            # chain start
            first = self.deadline_changes[0]
            if first.old_deadline != anchor:
                raise ValueError(
                    "deadline_changes chain must start from delivery_deadline_anchor"
                )

            # chain continuity
            prev = first
            for ch in self.deadline_changes[1:]:
                if ch.old_deadline != prev.new_deadline:
                    raise ValueError("deadline_changes chain is not continuous")
                prev = ch

            # current deadline must match last change
            if self.delivery_deadline != self.deadline_changes[-1].new_deadline:
                raise ValueError(
                    "delivery_deadline must match the most recent deadline change"
                )
        else:
            # No changes: deadline should equal anchor (especially important for BOOKED).
            if self.delivery_deadline != anchor and self.status is ProjectStatus.BOOKED:
                raise ValueError(
                    "BOOKED project delivery_deadline cannot differ from anchor without a manual change log"
                )

        # Core rule: BOOKED projects cannot drift without an explicit manual change.
        if self.status is ProjectStatus.BOOKED:
            if self.delivery_deadline != anchor and not self.deadline_changes:
                raise ValueError(
                    "BOOKED project delivery_deadline cannot differ from anchor without a manual change log"
                )

    def with_delivery_deadline(self, new_deadline: datetime) -> Project:
        """
        Normal (non-manual) update path.

        For BOOKED projects, deadline is immutable via this path.
        """
        if new_deadline.tzinfo is None:
            raise ValueError("delivery_deadline must be timezone-aware")

        if self.contract_start_date > new_deadline.date():
            raise ValueError("contract_start_date cannot be after delivery_deadline")

        if self.status is ProjectStatus.BOOKED:
            raise ProjectDeadlineImmutableError(
                "Cannot change delivery_deadline for a BOOKED project via non-manual update"
            )

        return replace(self, delivery_deadline=new_deadline)

    def change_delivery_deadline_manual(
        self,
        new_deadline: datetime,
        *,
        reason: str,
        changed_at: Optional[datetime] = None,
    ) -> Project:
        """
        Explicit manual deadline override with audit trail.

        This is the only supported way to change a BOOKED project's deadline.
        """
        if new_deadline.tzinfo is None:
            raise ValueError("delivery_deadline must be timezone-aware")

        if self.contract_start_date > new_deadline.date():
            raise ValueError("contract_start_date cannot be after delivery_deadline")

        if changed_at is None:
            changed_at = datetime.now(timezone.utc)
        else:
            if changed_at.tzinfo is None:
                raise ValueError("changed_at must be timezone-aware")

        change = DeadlineChange(
            changed_at=changed_at,
            old_deadline=self.delivery_deadline,
            new_deadline=new_deadline,
            reason=reason,
        )

        return replace(
            self,
            delivery_deadline=new_deadline,
            deadline_changes=self.deadline_changes + (change,),
        )


class ProjectNotFoundError(KeyError):
    pass


class ProjectRepository:
    """
    Repository boundary.

    Persistence-agnostic by design.
    """

    def add(self, project: Project) -> None:
        raise NotImplementedError

    def get(self, project_id: str) -> Project:
        raise NotImplementedError


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self) -> None:
        self._projects: Dict[str, Project] = {}

    def add(self, project: Project) -> None:
        self._projects[project.id] = project

    def get(self, project_id: str) -> Project:
        try:
            return self._projects[project_id]
        except KeyError as exc:
            raise ProjectNotFoundError(project_id) from exc
