from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional


class LedgerAppendOnlyError(RuntimeError):
    """Raised when attempting to mutate ledger history (update/delete)."""


class LedgerEntryNotFoundError(KeyError):
    pass


@dataclass(frozen=True)
class LedgerEntry:
    """
    Append-only ledger entry.

    Notes:
    - finished_hours may be negative to support compensating entries.
    - occurred_at must be timezone-aware for auditability.
    """

    id: str
    project_id: str
    finished_hours: float
    occurred_at: datetime
    note: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("LedgerEntry id must be non-empty")

        if not self.project_id.strip():
            raise ValueError("LedgerEntry project_id must be non-empty")

        if self.finished_hours == 0:
            raise ValueError("finished_hours must be non-zero (use a note-only event elsewhere)")

        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")


class LedgerRepository:
    """
    Repository boundary.

    Append-only by contract.
    """

    def add(self, entry: LedgerEntry) -> None:
        raise NotImplementedError

    def get(self, entry_id: str) -> LedgerEntry:
        raise NotImplementedError

    def list_entries(self, *, project_id: Optional[str] = None) -> List[LedgerEntry]:
        raise NotImplementedError

    # Intentionally exposed to make the "append-only" rule explicit/testable.
    def update(self, entry: LedgerEntry) -> None:
        raise LedgerAppendOnlyError("Ledger is append-only: update is not allowed")

    def delete(self, entry_id: str) -> None:
        raise LedgerAppendOnlyError("Ledger is append-only: delete is not allowed")


class InMemoryLedgerRepository(LedgerRepository):
    def __init__(self) -> None:
        self._by_id: Dict[str, LedgerEntry] = {}
        self._order: List[str] = []

    def add(self, entry: LedgerEntry) -> None:
        # Allow idempotent add of the same entry object; reject conflicting duplicates.
        if entry.id in self._by_id and self._by_id[entry.id] != entry:
            raise ValueError(f"Duplicate LedgerEntry id with different content: {entry.id}")

        if entry.id not in self._by_id:
            self._by_id[entry.id] = entry
            self._order.append(entry.id)

    def get(self, entry_id: str) -> LedgerEntry:
        try:
            return self._by_id[entry_id]
        except KeyError as exc:
            raise LedgerEntryNotFoundError(entry_id) from exc

    def list_entries(self, *, project_id: Optional[str] = None) -> List[LedgerEntry]:
        entries: Iterable[LedgerEntry] = (self._by_id[eid] for eid in self._order)
        if project_id is None:
            return list(entries)
        return [e for e in entries if e.project_id == project_id]
