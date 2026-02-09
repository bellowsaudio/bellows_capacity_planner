from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional, Set


class DayClosureAppendOnlyError(RuntimeError):
    """Raised when attempting to mutate closure history (update/delete)."""


class DayClosureNotFoundError(KeyError):
    pass


class DuplicateDayClosureForDateError(ValueError):
    """
    Raised when attempting to add a second DayClosure for the same date.

    Rationale:
    Ticket E2-T3 failure mode includes "partial closure states".
    A single date must have a single authoritative closure record.
    """


@dataclass(frozen=True)
class DayClosure:
    """
    Append-only record that a specific planning-day is closed.

    Fields:
      - id: stable identifier for this closure record
      - day: the planning date being closed
      - closed_at: timezone-aware audit timestamp
      - note: optional human note
    """

    id: str
    day: date
    closed_at: datetime
    note: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("DayClosure id must be non-empty")

        if self.closed_at.tzinfo is None:
            raise ValueError("closed_at must be timezone-aware")


class DayClosureRepository:
    """
    Repository boundary.

    Append-only by contract.
    """

    def add(self, closure: DayClosure) -> None:
        raise NotImplementedError

    def get(self, closure_id: str) -> DayClosure:
        raise NotImplementedError

    def list_closures(self) -> List[DayClosure]:
        raise NotImplementedError

    def find_by_day(self, day: date) -> Optional[DayClosure]:
        raise NotImplementedError

    # Explicit append-only rule, mirroring ledger.py.
    def update(self, closure: DayClosure) -> None:
        raise DayClosureAppendOnlyError("DayClosure is append-only: update is not allowed")

    def delete(self, closure_id: str) -> None:
        raise DayClosureAppendOnlyError("DayClosure is append-only: delete is not allowed")


class InMemoryDayClosureRepository(DayClosureRepository):
    def __init__(self) -> None:
        self._by_id: Dict[str, DayClosure] = {}
        self._by_day: Dict[date, str] = {}
        self._order: List[str] = []

    def add(self, closure: DayClosure) -> None:
        # Idempotent re-add of identical object; reject conflicting duplicates.
        if closure.id in self._by_id and self._by_id[closure.id] != closure:
            raise ValueError(f"Duplicate DayClosure id with different content: {closure.id}")

        # Reject a second closure for the same day (prevents partial closure states).
        if closure.day in self._by_day:
            existing_id = self._by_day[closure.day]
            existing = self._by_id[existing_id]
            if existing != closure:
                raise DuplicateDayClosureForDateError(
                    "Duplicate DayClosure for day "
                    f"{closure.day.isoformat()}: existing id={existing.id}, new id={closure.id}"
                )

        if closure.id not in self._by_id:
            self._by_id[closure.id] = closure
            self._by_day[closure.day] = closure.id
            self._order.append(closure.id)

    def get(self, closure_id: str) -> DayClosure:
        try:
            return self._by_id[closure_id]
        except KeyError as exc:
            raise DayClosureNotFoundError(closure_id) from exc

    def list_closures(self) -> List[DayClosure]:
        return [self._by_id[cid] for cid in self._order]

    def find_by_day(self, day: date) -> Optional[DayClosure]:
        cid = self._by_day.get(day)
        if cid is None:
            return None
        return self._by_id[cid]


def closed_days_from_closures(closures: Iterable[DayClosure]) -> Set[date]:
    """
    Read-model helper: derive the set of closed dates from closures.

    E2-T3 rule implemented:
      - Closed days are excluded from future "remaining days"
    """
    return {c.day for c in closures}
