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
