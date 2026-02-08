from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


class InvalidDateRangeError(ValueError):
    """Raised when an inclusive date range is invalid."""


@dataclass(frozen=True)
class InclusiveDateRange:
    """
    Canonical inclusive date range: [start_date, end_date] inclusive.

    - start_date == end_date occupies exactly one day
    - a 3-day window yields exactly 3 candidate days
    """

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise InvalidDateRangeError(
                f"Invalid inclusive date range: end_date {self.end_date} "
                f"is before start_date {self.start_date}."
            )

    def days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def iter_days(self):
        current = self.start_date
        while current <= self.end_date:
            yield current
            current += timedelta(days=1)

    def to_list(self) -> list[date]:
        return list(self.iter_days())
