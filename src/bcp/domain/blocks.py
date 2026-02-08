# src/bcp/domain/blocks.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List

from bcp.domain.block_types import BlockType
from bcp.domain.date_ranges import InclusiveDateRange, InvalidDateRangeError


class BlockOverlapError(ValueError):
    """Raised when a proposed block illegally overlaps an existing block."""


def _ranges_overlap(a: InclusiveDateRange, b: InclusiveDateRange) -> bool:
    """
    Inclusive range overlap.
    Overlap exists if max(starts) <= min(ends).
    """
    return max(a.start_date, b.start_date) <= min(a.end_date, b.end_date)


# Hard exclusion rules for AWAY_FROM_STUDIO overlaps.
# We allow AWAY to overlap RECORDING_WINDOW (it must, to remove capacity inside a window).
_FORBIDDEN_WITH_AWAY = {
    BlockType.INTERNAL_CORRECTIONS,
    BlockType.PUBLISHER_CORRECTIONS_WINDOW,
}


def _is_illegal_overlap(a: BlockType, b: BlockType) -> bool:
    """
    Returns True if block types a and b are forbidden to overlap.
    Only hard rules here; no auto-resolution.
    """
    if a == BlockType.AWAY_FROM_STUDIO and b in _FORBIDDEN_WITH_AWAY:
        return True
    if b == BlockType.AWAY_FROM_STUDIO and a in _FORBIDDEN_WITH_AWAY:
        return True
    return False


@dataclass(frozen=True, slots=True)
class Block:
    """
    Minimal real block for E1-T4.

    - Inclusive dates (validated via InclusiveDateRange)
    """
    block_type: BlockType
    date_range: InclusiveDateRange

    @property
    def start_date(self) -> date:
        return self.date_range.start_date

    @property
    def end_date(self) -> date:
        return self.date_range.end_date

    @classmethod
    def create(cls, block_type_raw: str, start_date: date, end_date: date) -> "Block":
        block_type = BlockType.parse(block_type_raw)
        # Canonical validation (E1-T2).
        try:
            dr = InclusiveDateRange(start_date=start_date, end_date=end_date)
        except InvalidDateRangeError as e:
            # Re-raise as-is to preserve loud clarity.
            raise
        return cls(block_type=block_type, date_range=dr)

    def overlaps(self, other: "Block") -> bool:
        return _ranges_overlap(self.date_range, other.date_range)


@dataclass
class BlockStore:
    """
    In-memory store for blocks with enforcement at add-time.

    Simple + inspectable.
    """
    _blocks: List[Block] = field(default_factory=list)

    def all_blocks(self) -> List[Block]:
        return list(self._blocks)

    def add(self, block: Block) -> None:
        # Hard-fail illegal overlaps; do not clip, shift, or merge.
        for existing in self._blocks:
            if block.overlaps(existing) and _is_illegal_overlap(block.block_type, existing.block_type):
                raise BlockOverlapError(
                    "Illegal overlap: "
                    f"{block.block_type.value} ({block.start_date.isoformat()}..{block.end_date.isoformat()}) "
                    f"overlaps {existing.block_type.value} ({existing.start_date.isoformat()}..{existing.end_date.isoformat()}). "
                    "AWAY_FROM_STUDIO is a hard exclusion for studio-required blocks."
                )
        self._blocks.append(block)
