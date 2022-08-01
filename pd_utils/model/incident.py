from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class Incident:
    incident_id: str
    incident_number: int
    title: str
    created_at: str
    status: str
    last_status_change_at: str
    has_priority: bool
    urgency: str

    @classmethod
    def build_from(cls, resp: dict[str, Any]) -> Incident:
        """Build Incident object from PagerDuty API response."""
        return cls(
            incident_id=resp["id"],
            incident_number=resp["incident_number"],
            title=resp["title"],
            created_at=resp["created_at"],
            status=resp["status"],
            last_status_change_at=resp["last_status_change_at"],
            has_priority=bool(resp["priority"]),
            urgency=resp["urgency"],
        )

    def as_dict(self) -> dict[str, Any]:
        """Convert object to dictionary."""
        return dataclasses.asdict(self)
