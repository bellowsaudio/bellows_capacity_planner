from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    BOOKED = "booked"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"


@dataclass(frozen=True)
class Project:
    """
    Canonical Project entity.

    A Project:
    - defines commercial intent (scope, priority, deadlines)
    - does NOT own time directly
    - is referenced by blocks and ledger entries
    """

    id: str
    name: str
    status: ProjectStatus
    planned_finished_hours: float
    contract_start_date: date
    delivery_deadline: datetime
    priority: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Project name must be non-empty")

        if self.planned_finished_hours < 0:
            raise ValueError("planned_finished_hours must be >= 0")

        if self.delivery_deadline.tzinfo is None:
            raise ValueError("delivery_deadline must be timezone-aware")

        if self.contract_start_date > self.delivery_deadline.date():
            raise ValueError(
                "contract_start_date cannot be after delivery_deadline"
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
