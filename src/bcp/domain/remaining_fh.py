# src/bcp/domain/remaining_fh.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from bcp.domain.ledger import LedgerEntry, total_finished_hours_for_project
from bcp.domain.projects import Project


class RemainingFinishedHoursNegativeError(ValueError):
    """
    Raised when recorded finished hours exceed the planned finished hours.

    This is an explicit error state (E4-T2); do not clamp or silently allow negatives.
    """


def compute_remaining_finished_hours(
    *,
    project: Project,
    ledger_entries: Iterable[LedgerEntry],
) -> float:
    """
    Compute remaining finished hours for a project.

    Rule (E4-T2):
      remaining_fh = planned_finished_hours - ledger_sum_for_project

    Raises:
      RemainingFinishedHoursNegativeError: if remaining_fh < 0
    """
    recorded = total_finished_hours_for_project(ledger_entries, project_id=project.id)
    remaining = project.planned_finished_hours - recorded

    if remaining < 0:
        raise RemainingFinishedHoursNegativeError(
            f"Remaining finished hours is negative for project {project.id}: "
            f"planned={project.planned_finished_hours}, recorded={recorded}, remaining={remaining}."
        )

    return remaining
