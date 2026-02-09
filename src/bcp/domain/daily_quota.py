# src/bcp/domain/daily_quota.py

from __future__ import annotations


class InfeasibleDailyQuotaError(ValueError):
    """
    Raised when a daily quota is mathematically infeasible.

    E4-T3 canonical case:
      - remaining_recordable_days == 0 AND remaining_fh > 0
    """


def compute_daily_quota_fh_per_day(
    *,
    remaining_fh: float,
    remaining_recordable_days: int,
) -> float:
    """
    Compute per-project daily quota (FH/day).

    Canonical rules (E4-T3):
      - quota = remaining_fh / remaining_recordable_days
      - If remaining_fh == 0: quota is 0 (even if days == 0)
      - If remaining_recordable_days == 0 and remaining_fh > 0: infeasible (explicit error)
      - No rounding, clamping, or silent handling of division by zero.
    """
    if remaining_recordable_days < 0:
        raise ValueError("remaining_recordable_days must be >= 0")

    if remaining_fh < 0:
        raise ValueError("remaining_fh must be >= 0 (negative remaining FH is handled earlier)")

    if remaining_fh == 0:
        return 0.0

    if remaining_recordable_days == 0:
        raise InfeasibleDailyQuotaError(
            "Infeasible daily quota: remaining_fh > 0 but remaining_recordable_days == 0. "
            f"remaining_fh={remaining_fh}."
        )

    return remaining_fh / remaining_recordable_days
