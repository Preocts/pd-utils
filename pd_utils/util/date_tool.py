from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from datetime import timedelta


class DateTool:
    @staticmethod
    def to_isotime(date_time: datetime) -> str:
        """Convert datetime to PD formated iso time"""
        return date_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def to_datetime(isotime: str) -> datetime:
        """Covert PD formated iso time to unaware datetime."""
        return datetime.fromisoformat(isotime.rstrip("Z"))

    @staticmethod
    def to_seconds(start: str, end: str) -> int:
        """Find the number of seconds between two PD formated iso times."""
        start_ = DateTool.to_datetime(start)
        end_ = DateTool.to_datetime(end)
        return int((end_ - start_).total_seconds())

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
    def _is_gapless(sorted_slots: list[tuple[str, str]]) -> bool:
        """
        Compare (start_time, end_time) PD timestamps, true if no gaps exist.

        NOTE: time_slots must be in desc order

        This method identifies if there is gaps between time slots but
        does not assert that a given time range is covered. The first
        and last time slot provided are assumed covered before and after.
        """
        has_coverage = bool(sorted_slots)

        _, prior_stop = sorted_slots.pop() if has_coverage else ("", "")
        while sorted_slots:

            start, stop = sorted_slots.pop()

            if start > prior_stop:
                has_coverage = False
                break

            prior_stop = stop

        return has_coverage

    @staticmethod
    def is_covered(
        time_slots: Sequence[tuple[str, str]],
        range_start: str,
        range_stop: str,
    ) -> bool:
        """
        Assert times between start and end have no gaps in coverage.

        Args:
            time_slots: Sequence of (start_time, end_time) PD timestamps, in any order
            range_start: PD timestamp of start for range to check
            range_stop: PD timesteamp of stop for range to check
        """
        # Sort by endtime in reverse
        sorted_slots = sorted(time_slots, key=lambda x: x[1], reverse=True)
        # Sort by starttime in reverse
        sorted_slots = sorted(sorted_slots, key=lambda x: x[0], reverse=True)

        if not DateTool._is_gapless(sorted_slots.copy()):
            return False

        first_start, _ = sorted_slots[-1]
        _, last_end = sorted_slots[0]

        return first_start <= range_start and range_stop <= last_end
