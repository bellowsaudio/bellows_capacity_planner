from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional, Set


class DayOverrideType(str, Enum):
    """
    Canonical day-level modifiers.

    E5-T1 introduces:
      - NO_RECORDING: excludes the day from remaining recordable days for that project.
    """

    NO_RECORDING = "NO_RECORDING"

    @classmethod
    def parse(cls, raw: str) -> "DayOverrideType":
        try:
            return cls(raw)
        except ValueError as e:
            allowed = ", ".join([m.value for m in cls])
            raise ValueError(f"Unknown DayOverrideType: {raw!r}. Allowed types: {allowed}.") from e


class DayOverrideAppendOnlyError(RuntimeError):
    """Raised when attempting to mutate override history (update/delete)."""


class DayOverrideNotFoundError(KeyError):
    pass


class DuplicateDayOverrideForDayError(ValueError):
    """
    Raised when attempting to add a conflicting override for the same (project_id, day, override_type).

    Rationale:
      - Prevents partial/inconsistent states in an append-only model.
      - Idempotent re-add of the same object remains allowed.
    """


@dataclass(frozen=True)
class DayOverride:
    """
    Append-only per-project day override.

    Fields:
      - id: stable identifier for the override record
      - project_id: project the override applies to
      - day: planning date affected
      - override_type: e.g. NO_RECORDING
      - set_at: timezone-aware audit timestamp
      - note: optional human note
    """

    id: str
    project_id: str
    day: date
    override_type: DayOverrideType
    set_at: datetime
    note: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("DayOverride id must be non-empty")

        if not self.project_id.strip():
            raise ValueError("DayOverride project_id must be non-empty")

        if self.set_at.tzinfo is None:
            raise ValueError("set_at must be timezone-aware")


class DayOverrideRepository:
    """
    Repository boundary.

    Append-only by contract.
    """

    def add(self, override: DayOverride) -> None:
        raise NotImplementedError

    def get(self, override_id: str) -> DayOverride:
        raise NotImplementedError

    def list_overrides(self, *, project_id: Optional[str] = None) -> List[DayOverride]:
        raise NotImplementedError

    def update(self, override: DayOverride) -> None:
        raise DayOverrideAppendOnlyError("DayOverride is append-only: update is not allowed")

    def delete(self, override_id: str) -> None:
        raise DayOverrideAppendOnlyError("DayOverride is append-only: delete is not allowed")


class InMemoryDayOverrideRepository(DayOverrideRepository):
    def __init__(self) -> None:
        self._by_id: Dict[str, DayOverride] = {}
        self._order: List[str] = []
        self._unique_key: Dict[tuple[str, date, DayOverrideType], str] = {}

    def add(self, override: DayOverride) -> None:
        # Idempotent re-add of identical object; reject conflicting duplicates by id.
        if override.id in self._by_id and self._by_id[override.id] != override:
            raise ValueError(f"Duplicate DayOverride id with different content: {override.id}")

        key = (override.project_id, override.day, override.override_type)
        if key in self._unique_key:
            existing_id = self._unique_key[key]
            existing = self._by_id[existing_id]
            if existing != override:
                raise DuplicateDayOverrideForDayError(
                    "Duplicate DayOverride for "
                    f"project_id={override.project_id}, day={override.day.isoformat()}, "
                    f"type={override.override_type.value}. existing id={existing.id}, new id={override.id}"
                )

        if override.id not in self._by_id:
            self._by_id[override.id] = override
            self._order.append(override.id)
            self._unique_key[key] = override.id

    def get(self, override_id: str) -> DayOverride:
        try:
            return self._by_id[override_id]
        except KeyError as exc:
            raise DayOverrideNotFoundError(override_id) from exc

    def list_overrides(self, *, project_id: Optional[str] = None) -> List[DayOverride]:
        overrides = [self._by_id[oid] for oid in self._order]
        if project_id is None:
            return overrides
        return [o for o in overrides if o.project_id == project_id]


def no_recording_days_for_project(overrides: Iterable[DayOverride], *, project_id: str) -> Set[date]:
    """
    Read-model helper: derive dates excluded by NO_RECORDING for a given project.
    """
    if not project_id.strip():
        raise ValueError("project_id must be non-empty")

    days: Set[date] = set()
    for o in overrides:
        if o.project_id == project_id and o.override_type is DayOverrideType.NO_RECORDING:
            days.add(o.day)
    return days
