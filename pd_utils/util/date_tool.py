from __future__ import annotations

from datetime import datetime
from datetime import timedelta


class DateTool:
    @staticmethod
    def to_isotime(date_time: datetime) -> str:
        """Convert datetime to PD formated iso time"""
        return date_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def add_offset(
        isotime: str,
        *,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> str:
        """Adjust string time by given amount"""
        dt = datetime.fromisoformat(isotime.rstrip("Z"))
        adjusted = dt + timedelta(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )
        return DateTool.to_isotime(adjusted)

    @staticmethod
    def utcnow_isotime() -> str:
        return DateTool.to_isotime(datetime.utcnow())

    @staticmethod
    def is_covered(time_slots: list[tuple[str, str]]) -> bool:
        """
        Compare (start_time, end_time) PD timestamps, true if fully covered.

        This method identifies if there is gaps between time slots but
        does not assert that a given time range is covered. The first
        and last time slot provided are assumed covered before and after.
        """
        has_coverage = True  # Always assume the best of people until proven otherwise.

        # Sort by starttime in reverse
        sorted_slots = sorted(time_slots, key=lambda x: x[0], reverse=True)

        _, prior_stop = sorted_slots.pop()
        while sorted_slots:

            start, stop = sorted_slots.pop()

            if start > prior_stop:
                has_coverage = False
                break

            prior_stop = stop

        return has_coverage
