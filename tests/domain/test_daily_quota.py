# tests/domain/test_daily_quota.py

import pytest

from bcp.domain.daily_quota import InfeasibleDailyQuotaError, compute_daily_quota_fh_per_day


def test_daily_quota_is_remaining_fh_divided_by_remaining_days():
    q = compute_daily_quota_fh_per_day(remaining_fh=10.0, remaining_recordable_days=4)
    assert q == 2.5


def test_daily_quota_zero_fh_is_zero_even_if_days_zero():
    q = compute_daily_quota_fh_per_day(remaining_fh=0.0, remaining_recordable_days=0)
    assert q == 0.0


def test_daily_quota_infeasible_when_days_zero_and_fh_positive():
    with pytest.raises(InfeasibleDailyQuotaError) as exc:
        compute_daily_quota_fh_per_day(remaining_fh=1.0, remaining_recordable_days=0)

    assert "infeasible" in str(exc.value).lower()


def test_daily_quota_rejects_negative_days():
    with pytest.raises(ValueError):
        compute_daily_quota_fh_per_day(remaining_fh=1.0, remaining_recordable_days=-1)


def test_daily_quota_rejects_negative_remaining_fh():
    with pytest.raises(ValueError):
        compute_daily_quota_fh_per_day(remaining_fh=-0.1, remaining_recordable_days=10)
