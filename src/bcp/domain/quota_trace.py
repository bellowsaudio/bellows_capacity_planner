from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import FrozenSet, Iterable, Optional, Sequence, Set

from bcp.domain.blocks import Block
from bcp.domain.daily_quota import InfeasibleDailyQuotaError, compute_daily_quota_fh_per_day
from bcp.domain.day_overrides import DayOverride
from bcp.domain.ledger import LedgerEntry
from bcp.domain.planning_parameters import PlanningParametersVersion
from bcp.domain.projects import Project
from bcp.domain.remaining_days import RemainingRecordableDaysResult, compute_remaining_recordable_days
from bcp.domain.remaining_fh import compute_remaining_finished_hours
from bcp.domain.time.moments import Moment


@dataclass(frozen=True, slots=True)
class DailyQuotaExplainabilityTrace:
    """
    Audit-grade trace for a single-project daily quota computation.

    This object is intended to make quota math reconstructable by hand.
    """

    project_id: str
    as_of_date: date

    remaining_fh: float
    remaining_recordable_days: int

    # Exclusions (day-based, explicit)
    excluded_away: FrozenSet[date]
    excluded_closed: FrozenSet[date]
    excluded_no_recording_override: FrozenSet[date]
    excluded_nonrecordable_final_day: FrozenSet[date]

    # Window evaluation facts
    window_start_date: date
    window_end_date: date
    evaluated_start_date: date
    evaluated_end_date: date

    # Parameters used (explicit version)
    parameter_version_id: str
    baseline_fh_per_day: float
    stretch_fh_per_day: float

    # Deadline moment (time-truth anchor)
    deadline_moment: Moment

    # Output
    quota_fh_per_day: float


@dataclass(frozen=True, slots=True)
class DailyQuotaWithTrace:
    quota_fh_per_day: float
    trace: DailyQuotaExplainabilityTrace


class InfeasibleDailyQuotaWithTraceError(InfeasibleDailyQuotaError):
    """
    Raised when quota is infeasible, carrying a full explainability trace.
    """

    def __init__(self, message: str, trace: DailyQuotaExplainabilityTrace) -> None:
        super().__init__(message)
        self.trace = trace


def compute_daily_quota_with_trace(
    *,
    project: Project,
    as_of_date: date,
    blocks: Sequence[Block],
    ledger_entries: Iterable[LedgerEntry],
    parameters_version: PlanningParametersVersion,
    closed_days: Optional[Set[date]] = None,
    day_overrides: Optional[Sequence[DayOverride]] = None,
) -> DailyQuotaWithTrace:
    """
    Compute per-project daily quota (FH/day) plus a full explainability trace.

    Notes:
    - No silent defaults: caller must pass the parameter version explicitly.
    - Closed days / overrides default only to "no exclusions provided" containers,
      which preserves existing domain behaviour and avoids coercion.
    """
    remaining_fh = compute_remaining_finished_hours(project=project, ledger_entries=ledger_entries)

    remaining_days_result: RemainingRecordableDaysResult = compute_remaining_recordable_days(
        project=project,
        as_of_date=as_of_date,
        blocks=blocks,
        closed_days=closed_days,
        day_overrides=day_overrides,
    )

    deadline_moment = Moment.from_aware(project.delivery_deadline)

    # Compute quota using the canonical quota function; if infeasible, raise
    # an explicit error carrying the trace.
    try:
        quota = compute_daily_quota_fh_per_day(
            remaining_fh=remaining_fh,
            remaining_recordable_days=remaining_days_result.remaining_recordable_days,
        )
    except InfeasibleDailyQuotaError as exc:
        trace = DailyQuotaExplainabilityTrace(
            project_id=project.id,
            as_of_date=as_of_date,
            remaining_fh=remaining_fh,
            remaining_recordable_days=remaining_days_result.remaining_recordable_days,
            excluded_away=remaining_days_result.excluded_away,
            excluded_closed=remaining_days_result.excluded_closed,
            excluded_no_recording_override=remaining_days_result.excluded_no_recording_override,
            excluded_nonrecordable_final_day=remaining_days_result.excluded_nonrecordable_final_day,
            window_start_date=remaining_days_result.window.start_date,
            window_end_date=remaining_days_result.window.end_date,
            evaluated_start_date=remaining_days_result.evaluated_start_date,
            evaluated_end_date=remaining_days_result.evaluated_end_date,
            parameter_version_id=parameters_version.id,
            baseline_fh_per_day=parameters_version.baseline_fh_per_day,
            stretch_fh_per_day=parameters_version.stretch_fh_per_day,
            deadline_moment=deadline_moment,
            quota_fh_per_day=0.0,
        )
        raise InfeasibleDailyQuotaWithTraceError(str(exc), trace=trace) from exc

    trace = DailyQuotaExplainabilityTrace(
        project_id=project.id,
        as_of_date=as_of_date,
        remaining_fh=remaining_fh,
        remaining_recordable_days=remaining_days_result.remaining_recordable_days,
        excluded_away=remaining_days_result.excluded_away,
        excluded_closed=remaining_days_result.excluded_closed,
        excluded_no_recording_override=remaining_days_result.excluded_no_recording_override,
        excluded_nonrecordable_final_day=remaining_days_result.excluded_nonrecordable_final_day,
        window_start_date=remaining_days_result.window.start_date,
        window_end_date=remaining_days_result.window.end_date,
        evaluated_start_date=remaining_days_result.evaluated_start_date,
        evaluated_end_date=remaining_days_result.evaluated_end_date,
        parameter_version_id=parameters_version.id,
        baseline_fh_per_day=parameters_version.baseline_fh_per_day,
        stretch_fh_per_day=parameters_version.stretch_fh_per_day,
        deadline_moment=deadline_moment,
        quota_fh_per_day=quota,
    )

    return DailyQuotaWithTrace(quota_fh_per_day=quota, trace=trace)
