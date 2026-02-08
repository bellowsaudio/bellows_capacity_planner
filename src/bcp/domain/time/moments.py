# src/bcp/domain/time/moments.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


# Canonical planning timezone: "GMT, DST-aware" == Europe/London in practice.
PLANNING_TZ = ZoneInfo("Europe/London")

# Default contractual deadline timezone + local clock time (Stage 3 canonical).
DEFAULT_DEADLINE_TZ = ZoneInfo("America/New_York")
DEFAULT_DEADLINE_LOCAL_TIME = time(17, 0)

UTC = ZoneInfo("UTC")


def _is_ambiguous_local_time(tz: ZoneInfo, naive_dt: datetime) -> bool:
    """
    Returns True if naive_dt is ambiguous in tz (DST fall-back overlap).
    We detect ambiguity by comparing offsets with fold=0 vs fold=1.
    """
    if naive_dt.tzinfo is not None:
        raise ValueError("naive_dt must be naive (tzinfo=None) for ambiguity check.")

    dt0 = naive_dt.replace(tzinfo=tz, fold=0)
    dt1 = naive_dt.replace(tzinfo=tz, fold=1)
    return dt0.utcoffset() != dt1.utcoffset()


def _is_nonexistent_local_time(tz: ZoneInfo, naive_dt: datetime) -> bool:
    """
    Returns True if naive_dt is nonexistent in tz (DST spring-forward gap).

    Strategy:
    - Attach tzinfo (fold=0)
    - Convert to UTC and back to tz
    - If the wall-clock time changes, the original wall time wasn't real
      (it got normalized into a different time).
    """
    if naive_dt.tzinfo is not None:
        raise ValueError("naive_dt must be naive (tzinfo=None) for existence check.")

    aware = naive_dt.replace(tzinfo=tz, fold=0)
    roundtrip = aware.astimezone(UTC).astimezone(tz)
    return roundtrip.replace(tzinfo=None) != naive_dt


def _assert_valid_local_wall_time(tz: ZoneInfo, naive_dt: datetime) -> None:
    if _is_ambiguous_local_time(tz, naive_dt):
        raise ValueError(
            f"Ambiguous local time in timezone {tz.key}: {naive_dt.isoformat()} "
            "(DST fall-back overlap). Provide an explicit instant instead."
        )
    if _is_nonexistent_local_time(tz, naive_dt):
        raise ValueError(
            f"Nonexistent local time in timezone {tz.key}: {naive_dt.isoformat()} "
            "(DST spring-forward gap). Provide an explicit instant instead."
        )


@dataclass(frozen=True, slots=True)
class Moment:
    """
    A timezone-aware instant with strict invariants.

    - Must be created from an aware datetime (no naive datetimes).
    - Normalized to UTC internally for stable comparison/storage.
    """
    _utc_dt: datetime

    def __post_init__(self) -> None:
        if self._utc_dt.tzinfo is None:
            raise ValueError("Moment requires a timezone-aware datetime (tzinfo must not be None).")
        object.__setattr__(self, "_utc_dt", self._utc_dt.astimezone(UTC))

    @classmethod
    def from_aware(cls, dt: datetime) -> "Moment":
        if dt.tzinfo is None:
            raise ValueError("from_aware() requires a timezone-aware datetime.")
        return cls(dt)

    @classmethod
    def from_local(cls, local_date: date, local_time: time, tz: ZoneInfo) -> "Moment":
        """
        Construct a Moment from a date+time interpreted in a specific timezone.

        Loudly fails on ambiguous or nonexistent wall times.
        """
        naive = datetime.combine(local_date, local_time)
        _assert_valid_local_wall_time(tz, naive)
        aware = naive.replace(tzinfo=tz, fold=0)
        return cls(aware)

    def to_utc_dt(self) -> datetime:
        return self._utc_dt

    def to_planning_dt(self) -> datetime:
        return self._utc_dt.astimezone(PLANNING_TZ)


def default_contract_deadline(delivery_date: date) -> Moment:
    """
    Stage-3 canonical default: 17:00 America/New_York on the delivery date.
    """
    return Moment.from_local(delivery_date, DEFAULT_DEADLINE_LOCAL_TIME, DEFAULT_DEADLINE_TZ)


def effective_window_end_date(delivery_date: date, deadline: Moment) -> date:
    """
    Stage-3 canonical "no ghost day":
    The inclusive planning window end-date is ALWAYS the stated delivery_date,
    regardless of how the deadline instant converts into the planning timezone.

    deadline is accepted to make the rule explicit at call sites, but does not alter the result.
    """
    if not isinstance(deadline, Moment):
        raise TypeError("deadline must be a Moment.")
    return delivery_date
