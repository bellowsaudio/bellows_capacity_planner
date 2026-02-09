# src/bcp/domain/daily_load.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, FrozenSet, Iterable, Optional, Sequence, Set

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


@dataclass(frozen=True, slots=True)
class DailyLoadResult:
    """
    E4-T4 output container.

    - daily: day-indexed load model (includes zero-load days in the horizon)
    - errors: explicit failure states (infeasible quota, negative remaining FH, etc.)
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

    Horizon:
      - from as_of_date through the latest project window end-date (inclusive).
      - includes days with zero load (inspectable).

    Closed days:
      - not yet modelled elsewhere; default is empty set (freelancer assumption).
      - days become non-recordable only if explicitly blocked (e.g. AWAY_FROM_STUDIO).
    """
    if closed_days is None:
        closed_days = set()

    if not projects:
        return DailyLoadResult(daily={}, errors=())

    horizon_start = as_of_date
    horizon_end = max(recording_window_for_project(p).end_date for p in projects)

    if horizon_start > horizon_end:
        return DailyLoadResult(daily={}, errors=())

    # Precompute away days once; apply per-project membership checks by date.
    away_days = _days_covered_by_blocks(blocks, BlockType.AWAY_FROM_STUDIO)

    # Compute per-project quota and recordable-day membership.
    quotas_by_project: Dict[str, float] = {}
    recordable_days_by_project: Dict[str, FrozenSet[date]] = {}
    errors: list[DailyLoadComputationError] = []

    ledger_list = list(ledger_entries)  # ensure single-pass iterables are safe

    for p in projects:
        window = recording_window_for_project(p)
        if window.end_date < as_of_date:
            # Project entirely in the past relative to this planning run.
            quotas_by_project[p.id] = 0.0
            recordable_days_by_project[p.id] = frozenset()
            continue

        # Recordable days for this project in the evaluated portion of the window.
        recordable_days = _recordable_days_for_project(
            project=p,
            as_of_date=as_of_date,
            blocks=blocks,
            away_days=away_days,
            closed_days=closed_days,
        )
        recordable_days_by_project[p.id] = recordable_days

        # Remaining FH (explicit error if negative).
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

        # Daily quota (explicit infeasible if days == 0 and FH > 0).
        try:
            quota = compute_daily_quota_fh_per_day(
                remaining_fh=remaining_fh,
                remaining_recordable_days=len(recordable_days),
            )
        except InfeasibleDailyQuotaError as e:
            errors.append(
                DailyLoadComputationError(
                    project_id=p.id,
                    error_type="quota_infeasible",
                    message=str(e),
                )
            )
            quotas_by_project[p.id] = 0.0
            continue

        quotas_by_project[p.id] = quota

    # Aggregate per-day load.
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
    # date arithmetic without importing timedelta at top-level (keeps imports tight)
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
