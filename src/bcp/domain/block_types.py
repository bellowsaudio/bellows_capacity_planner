from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class UnknownBlockTypeError(ValueError):
    """Raised when a block type is not part of the canonical closed registry."""


class BlockType(str, Enum):
    """
    Canonical closed registry of block types (Stage-2 aligned).

    IMPORTANT:
    - No free-text block types.
    - No silent coercion.
    - Any unknown type must fail loudly.
    """

    RECORDING_WINDOW = "RECORDING_WINDOW"
    INTERNAL_CORRECTIONS = "INTERNAL_CORRECTIONS"
    SICK_BUFFER = "SICK_BUFFER"
    PUBLISHER_CORRECTIONS_WINDOW = "PUBLISHER_CORRECTIONS_WINDOW"
    AWAY_FROM_STUDIO = "AWAY_FROM_STUDIO"

    @classmethod
    def parse(cls, raw: str) -> "BlockType":
        """
        Parse a user/system provided string into a BlockType.

        Raises:
            UnknownBlockTypeError: if raw is not an exact member value.
        """
        try:
            return cls(raw)
        except ValueError as e:
            allowed = ", ".join([m.value for m in cls])
            raise UnknownBlockTypeError(
                f"Unknown block type: {raw!r}. Allowed types: {allowed}."
            ) from e


@dataclass(frozen=True)
class BlockTypeOnly:
    """
    Minimal 'block' placeholder for E1-T1.

    We intentionally only model type here to satisfy the ticket's scope.
    (Dates, overlaps, timezone rules are later tickets.)
    """

    block_type: BlockType

    @classmethod
    def create(cls, block_type_raw: str) -> "BlockTypeOnly":
        return cls(block_type=BlockType.parse(block_type_raw))
