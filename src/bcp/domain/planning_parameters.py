from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PlanningParametersVersion:
    """
    Immutable planning parameters snapshot.

    A new version must be created for any edit; old versions remain intact.
    """

    id: str
    created_at: datetime
    baseline_fh_per_day: float
    stretch_fh_per_day: float

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("PlanningParametersVersion id must be non-empty")

        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")

        if self.baseline_fh_per_day <= 0:
            raise ValueError("baseline_fh_per_day must be > 0")

        if self.stretch_fh_per_day <= 0:
            raise ValueError("stretch_fh_per_day must be > 0")

        if self.stretch_fh_per_day < self.baseline_fh_per_day:
            raise ValueError("stretch_fh_per_day must be >= baseline_fh_per_day")


class PlanningParametersNotFoundError(KeyError):
    pass


class PlanningParametersRepository:
    """
    Repository boundary for parameter versions.
    """

    def add_version(self, version: PlanningParametersVersion) -> None:
        raise NotImplementedError

    def get_version(self, version_id: str) -> PlanningParametersVersion:
        raise NotImplementedError

    def latest_version(self) -> PlanningParametersVersion:
        raise NotImplementedError

    def list_versions(self) -> List[PlanningParametersVersion]:
        raise NotImplementedError


class InMemoryPlanningParametersRepository(PlanningParametersRepository):
    def __init__(self) -> None:
        self._by_id: Dict[str, PlanningParametersVersion] = {}
        self._order: List[str] = []

    def add_version(self, version: PlanningParametersVersion) -> None:
        # Allow idempotent re-add of identical object; reject conflicting duplicates.
        if version.id in self._by_id and self._by_id[version.id] != version:
            raise ValueError(
                f"Duplicate PlanningParametersVersion id with different content: {version.id}"
            )

        if version.id not in self._by_id:
            self._by_id[version.id] = version
            self._order.append(version.id)

    def get_version(self, version_id: str) -> PlanningParametersVersion:
        try:
            return self._by_id[version_id]
        except KeyError as exc:
            raise PlanningParametersNotFoundError(version_id) from exc

    def latest_version(self) -> PlanningParametersVersion:
        if not self._order:
            raise PlanningParametersNotFoundError("No planning parameters versions exist")
        return self._by_id[self._order[-1]]

    def list_versions(self) -> List[PlanningParametersVersion]:
        return [self._by_id[vid] for vid in self._order]


def create_new_version(
    *,
    version_id: str,
    baseline_fh_per_day: float,
    stretch_fh_per_day: float,
    created_at: Optional[datetime] = None,
) -> PlanningParametersVersion:
    """
    Helper constructor with sane default timestamp.
    """
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return PlanningParametersVersion(
        id=version_id,
        created_at=created_at,
        baseline_fh_per_day=baseline_fh_per_day,
        stretch_fh_per_day=stretch_fh_per_day,
    )


def edit_parameters_creates_new_version(
    *,
    prior: PlanningParametersVersion,
    version_id: str,
    baseline_fh_per_day: Optional[float] = None,
    stretch_fh_per_day: Optional[float] = None,
    created_at: Optional[datetime] = None,
) -> PlanningParametersVersion:
    """
    Produce a new immutable version based on a prior version.

    This is the canonical "edit" operation: no mutation of the prior version.
    """
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    return PlanningParametersVersion(
        id=version_id,
        created_at=created_at,
        baseline_fh_per_day=prior.baseline_fh_per_day
        if baseline_fh_per_day is None
        else baseline_fh_per_day,
        stretch_fh_per_day=prior.stretch_fh_per_day
        if stretch_fh_per_day is None
        else stretch_fh_per_day,
    )
