from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, FrozenSet, Iterable, Optional, Sequence, Set, Tuple

from bcp.domain.block_types import BlockType
from bcp.domain.blocks import Block
from bcp.domain.daily_quota import InfeasibleDailyQuotaError, compute_daily_quota_fh_per_day
from bcp.domain.ledger import LedgerEntry
from bcp.domain.planning_parameters import PlanningParametersVersion
from bcp.domain.projects import Project
from bcp.domain.remaining_days import recording_window_for_project
from bcp.domain.remaining_fh import (
    RemainingFinishedHoursNegativeError,
    compute_remaining_finished_hours,
)


@dataclass(frozen=True, slots=True)
class DailyLoad:
    """
    Per-day total load across all projects.

    Flags are purely informational:
    - no auto-stretch
    - no hiding overload
    """
    day: date
    total_fh: float
    exceeds_baseline: bool
    exceeds_stretch: bool


@dataclass(frozen=True, slots=True)
class DailyLoadComputationError:
    """
    Non-ignorable project-level failure surfaced at the day/load layer.

    We keep this explicit instead of silently skipping projects.
    """
    project_id: str
    error_type: str
    message: str


class InfeasiblePlanError(RuntimeError):
    """
    Raised when at least one project is infeasible (FH remaining with zero recordable days).

    E10-T1 rule:
      Infeasible states must be explicit and unignorable.
    """

    def __init__(self, *, errors: Tuple[DailyLoadComputationError, ...]) -> None:
        self.errors = errors
        super().__init__(self._format(errors))

    @staticmethod
    def _format(errors: Tuple[DailyLoadComputationError, ...]) -> str:
        parts = []
        for e in errors:
            parts.append(f"{e.project_id}: {e.error_type}: {e.message}")
        return "Infeasible plan detected:\n" + "\n".join(parts)


@dataclass(frozen=True, slots=True)
class DailyLoadResult:
    """
    E4-T4 output container.

    - daily: day-indexed load model (includes zero-load days in the horizon)
    - errors: explicit failure states (negative remaining FH, etc.)

    Note:
      - E10-T1 elevates infeasible quota states to an exception, so they will not appear here.
    """
    daily: Dict[date, DailyLoad]
    errors: tuple[DailyLoadComputationError, ...]


def compute_daily_load(
    *,
    projects: Sequence[Project],
    as_of_date: date,
    ledger_entries: Iterable[LedgerEntry],
    blocks: Sequence[Block],
    planning_parameters: PlanningParametersVersion,
    closed_days: Optional[Set[date]] = None,
) -> DailyLoadResult:
    """
    Compute total daily load across all projects for a horizon.

    E4-T4 rules:
      - Total daily load is the SUM of per-project daily quotas on days where that project
        is recordable.
      - Baseline/stretch are global per-day thresholds across ALL projects.
      - Overload is flagged; never auto-resolved.

    E10-T1:
      - If any project is infeasible (FH remaining with zero recordable days), raise
        InfeasiblePlanError (explicit and unignorable).

    Horizon:
      - from as_of_date through the latest project window end-date (inclusive).
      - includes days with zero load (inspectable).
    """
    if closed_days is None:
        closed_days = set()

    if not projects:
        return DailyLoadResult(daily={}, errors=())

    horizon_start = as_of_date
    horizon_end = max(recording_window_for_project(p).end_date for p in projects)

    if horizon_start > horizon_end:
        return DailyLoadResult(daily={}, errors=())

    away_days = _days_covered_by_blocks(blocks, BlockType.AWAY_FROM_STUDIO)

    quotas_by_project: Dict[str, float] = {}
    recordable_days_by_project: Dict[str, FrozenSet[date]] = {}
    errors: list[DailyLoadComputationError] = []
    infeasible_errors: list[DailyLoadComputationError] = []

    ledger_list = list(ledger_entries)

    for p in projects:
        window = recording_window_for_project(p)
        if window.end_date < as_of_date:
            quotas_by_project[p.id] = 0.0
            recordable_days_by_project[p.id] = frozenset()
            continue

        recordable_days = _recordable_days_for_project(
            project=p,
            as_of_date=as_of_date,
            blocks=blocks,
            away_days=away_days,
            closed_days=closed_days,
        )
        recordable_days_by_project[p.id] = recordable_days

        try:
            remaining_fh = compute_remaining_finished_hours(
                project=p,
                ledger_entries=ledger_list,
            )
        except RemainingFinishedHoursNegativeError as e:
            errors.append(
                DailyLoadComputationError(
                    project_id=p.id,
                    error_type="remaining_fh_negative",
                    message=str(e),
                )
            )
            quotas_by_project[p.id] = 0.0
            continue

        try:
            quota = compute_daily_quota_fh_per_day(
                remaining_fh=remaining_fh,
                remaining_recordable_days=len(recordable_days),
            )
        except InfeasibleDailyQuotaError as e:
            err = DailyLoadComputationError(
                project_id=p.id,
                error_type="quota_infeasible",
                message=str(e),
            )
            infeasible_errors.append(err)
            quotas_by_project[p.id] = 0.0
            continue

        quotas_by_project[p.id] = quota

    # E10-T1: infeasible states are explicit and unignorable.
    if infeasible_errors:
        raise InfeasiblePlanError(errors=tuple(infeasible_errors))

    daily: Dict[date, DailyLoad] = {}
    current = horizon_start
    while current <= horizon_end:
        total = 0.0
        for p in projects:
            if current in recordable_days_by_project.get(p.id, frozenset()):
                total += quotas_by_project.get(p.id, 0.0)

        daily[current] = DailyLoad(
            day=current,
            total_fh=total,
            exceeds_baseline=total > planning_parameters.baseline_fh_per_day,
            exceeds_stretch=total > planning_parameters.stretch_fh_per_day,
        )
        current = _add_one_day(current)

    return DailyLoadResult(daily=daily, errors=tuple(errors))


# --- internal helpers (domain-scoped, not "utils") ---


def _add_one_day(d: date) -> date:
    from datetime import timedelta
    return d + timedelta(days=1)


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


def _recordable_days_for_project(
    *,
    project: Project,
    as_of_date: date,
    blocks: Sequence[Block],
    away_days: Set[date],
    closed_days: Set[date],
) -> FrozenSet[date]:
    window = recording_window_for_project(project)
    start = max(as_of_date, window.start_date)
    end = window.end_date

    if start > end:
        return frozenset()

    final_day_excluded = _final_day_is_blocked(end, blocks)

    recordable: Set[date] = set()
    current = start
    while current <= end:
        if current in away_days:
            current = _add_one_day(current)
            continue
        if current in closed_days:
            current = _add_one_day(current)
            continue
        if final_day_excluded and current == end:
            current = _add_one_day(current)
            continue

        recordable.add(current)
        current = _add_one_day(current)

    return frozenset(recordable)
