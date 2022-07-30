from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass(frozen=True)
class ScheduleCoverage:
    pd_id: str
    name: str
    html_url: str
    coverage: float

    @classmethod
    def build_from(cls, resp: dict[str, Any]) -> ScheduleCoverage:
        """Build model from API response of PagerDuty."""
        final = resp["schedule"].get("final_schedule") or {}
        return cls(
            pd_id=resp["schedule"].get("id") or "",
            name=resp["schedule"].get("name") or "",
            html_url=resp["schedule"].get("html_url") or "",
            coverage=final.get("rendered_coverage_percentage") or 0.0,
        )

    def as_dict(self) -> dict[str, Any]:
        """Render model as dict."""
        return dataclasses.asdict(self)
