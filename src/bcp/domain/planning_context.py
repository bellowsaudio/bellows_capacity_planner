from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PlanningContextVersionPointer:
    """
    Append-only record of which PlanningParametersVersion is considered "active".

    Rationale:
    - We preserve history of changes to "active" parameters (auditability).
    - The current active version is the latest pointer.
    """

    id: str
    active_version_id: str
    set_at: datetime
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("PlanningContextVersionPointer id must be non-empty")

        if not self.active_version_id.strip():
            raise ValueError("active_version_id must be non-empty")

        if self.set_at.tzinfo is None:
            raise ValueError("set_at must be timezone-aware")


class PlanningContextNotFoundError(KeyError):
    pass


class PlanningContextRepository:
    def add_pointer(self, pointer: PlanningContextVersionPointer) -> None:
        raise NotImplementedError

    def get_pointer(self, pointer_id: str) -> PlanningContextVersionPointer:
        raise NotImplementedError

    def latest_pointer(self) -> PlanningContextVersionPointer:
        raise NotImplementedError

    def list_pointers(self) -> List[PlanningContextVersionPointer]:
        raise NotImplementedError


class InMemoryPlanningContextRepository(PlanningContextRepository):
    def __init__(self) -> None:
        self._by_id: Dict[str, PlanningContextVersionPointer] = {}
        self._order: List[str] = []

    def add_pointer(self, pointer: PlanningContextVersionPointer) -> None:
        # Allow idempotent re-add of identical object; reject conflicting duplicates.
        if pointer.id in self._by_id and self._by_id[pointer.id] != pointer:
            raise ValueError(
                f"Duplicate PlanningContextVersionPointer id with different content: {pointer.id}"
            )

        if pointer.id not in self._by_id:
            self._by_id[pointer.id] = pointer
            self._order.append(pointer.id)

    def get_pointer(self, pointer_id: str) -> PlanningContextVersionPointer:
        try:
            return self._by_id[pointer_id]
        except KeyError as exc:
            raise PlanningContextNotFoundError(pointer_id) from exc

    def latest_pointer(self) -> PlanningContextVersionPointer:
        if not self._order:
            raise PlanningContextNotFoundError("No planning context pointers exist")
        return self._by_id[self._order[-1]]

    def list_pointers(self) -> List[PlanningContextVersionPointer]:
        return [self._by_id[pid] for pid in self._order]


def set_active_planning_parameters(
    *,
    pointer_id: str,
    active_version_id: str,
    set_at: Optional[datetime] = None,
    reason: str = "",
) -> PlanningContextVersionPointer:
    """
    Helper constructor with sane default timestamp.
    """
    if set_at is None:
        set_at = datetime.now(timezone.utc)
    return PlanningContextVersionPointer(
        id=pointer_id,
        active_version_id=active_version_id,
        set_at=set_at,
        reason=reason,
    )
