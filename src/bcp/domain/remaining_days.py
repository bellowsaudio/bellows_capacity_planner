# src/bcp/domain/remaining_days.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import FrozenSet, Iterable, Optional, Sequence, Set

from bcp.domain.block_types import BlockType
from bcp.domain.blocks import Block
from bcp.domain.date_ranges import InclusiveDateRange
from bcp.domain.projects import Project
from bcp.domain.time.moments import Moment, effective_window_end_date


@dataclass(frozen=True, slots=True)
class RemainingRecordableDaysResult:
    """
    Result object kept intentionally small for E4-T1.

    We keep excluded day sets to support later E10 explainability
    without changing the core math signature again.
    """

    remaining_recordable_days: int
    window: InclusiveDateRange
    evaluated_start_date: date
    evaluated_end_date: date
    excluded_away: FrozenSet[date]
    excluded_closed: FrozenSet[date]
    excluded_nonrecordable_final_day: FrozenSet[date]


def recording_window_for_project(project: Project) -> InclusiveDateRange:
    """
    Canonical project recording window for capacity math.

    Start:
      - project.contract_start_date

    End:
      - Stage-3 canonical "no ghost day" end date derived from the delivery date,
        not from the converted planning-time instant.
    """
    deadline = Moment.from_aware(project.delivery_deadline)
    delivery_date = project.delivery_deadline.date()
    end_date = effective_window_end_date(delivery_date, deadline)
    return InclusiveDateRange(start_date=project.contract_start_date, end_date=end_date)


def compute_remaining_recordable_days(
    *,
    project: Project,
    as_of_date: date,
    blocks: Sequence[Block],
    closed_days: Optional[Set[date]] = None,
) -> RemainingRecordableDaysResult:
    """
    Compute remaining recordable days for a single project.

    E4-T1 rules implemented (strict, inspectable):
      - Candidate days are days inside the project's RECORDING_WINDOW (inclusive),
        but only from max(as_of_date, window.start_date) onward.
      - Subtract:
          - AWAY_FROM_STUDIO
          - closed days
          - (DayOverride(NO_RECORDING) will be added in E5-T1; not implemented here)
      - Endpoints never move (no sliding deadlines).
      - Final day is counted only if explicitly recordable.
        For E4-T1 we interpret "not explicitly recordable" as:
          - the final day is covered by a known "buffer-like" block type.

    Notes:
      - All evaluation here is day-based (date objects).
      - Planning timezone day-iteration is already enforced by using dates and the
        Stage-3 "no ghost day" window end-date rule in time/moments.py.
    """
    if closed_days is None:
        closed_days = set()

    window = recording_window_for_project(project)

    evaluated_start = max(as_of_date, window.start_date)
    evaluated_end = window.end_date

    # If we're already past the end, there are no remaining recordable days.
    if evaluated_start > evaluated_end:
        return RemainingRecordableDaysResult(
            remaining_recordable_days=0,
            window=window,
            evaluated_start_date=evaluated_start,
            evaluated_end_date=evaluated_end,
            excluded_away=frozenset(),
            excluded_closed=frozenset(),
            excluded_nonrecordable_final_day=frozenset(),
        )

    away_days = _days_covered_by_blocks(blocks, BlockType.AWAY_FROM_STUDIO)

    # Final-day explicit-recordable rule:
    # If the final day is covered by a "buffer-like" block, we exclude it.
    # (E5 will add explicit overrides; E4-T1 keeps this loud and simple.)
    final_day = evaluated_end
    final_day_excluded = set()

    if _final_day_is_blocked(final_day, blocks):
        final_day_excluded.add(final_day)

    recordable_count = 0
    excluded_away = set()
    excluded_closed = set()
    excluded_final = set()

    for d in InclusiveDateRange(evaluated_start, evaluated_end).iter_days():
        if d in away_days:
            excluded_away.add(d)
            continue

        if d in closed_days:
            excluded_closed.add(d)
            continue

        if d in final_day_excluded:
            excluded_final.add(d)
            continue

        recordable_count += 1

    return RemainingRecordableDaysResult(
        remaining_recordable_days=recordable_count,
        window=window,
        evaluated_start_date=evaluated_start,
        evaluated_end_date=evaluated_end,
        excluded_away=frozenset(excluded_away),
        excluded_closed=frozenset(excluded_closed),
        excluded_nonrecordable_final_day=frozenset(excluded_final),
    )


# --- internal helpers (domain-scoped, not "utils") ---


def _days_covered_by_blocks(blocks: Sequence[Block], block_type: BlockType) -> Set[date]:
    days: Set[date] = set()
    for b in blocks:
        if b.block_type is block_type:
            for d in b.date_range.iter_days():
                days.add(d)
    return days


_BUFFER_LIKE_TYPES: FrozenSet[BlockType] = frozenset(
    {
        BlockType.SICK_BUFFER,
        BlockType.INTERNAL_CORRECTIONS,
        BlockType.PUBLISHER_CORRECTIONS_WINDOW,
    }
)


def _final_day_is_blocked(final_day: date, blocks: Sequence[Block]) -> bool:
    for b in blocks:
        if b.block_type in _BUFFER_LIKE_TYPES:
            if b.start_date <= final_day <= b.end_date:
                return True
    return False
