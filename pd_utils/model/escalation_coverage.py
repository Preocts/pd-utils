"""Model escalation policy gap coverage."""
from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class _Rule:
    index: int
    target_names: tuple[str, ...]
    target_ids: tuple[str, ...]
    has_gaps: bool | None = None


@dataclasses.dataclass
class EscalationCoverage:
    ep_id: str
    name: str
    html_url: str
    rules: list[_Rule]

    @classmethod
    def build_from(cls, resp: dict[str, Any]) -> EscalationCoverage:
        """Build object from PagerDuty escalation_policies response."""
        rules: list[_Rule] = []
        for idx, rule in enumerate(resp["escalation_rules"] or [], 1):
            names = [
                t["summary"]
                for t in rule["targets"] or []
                if t["type"] == "schedule_reference"
            ]
            targets = [
                t["id"]
                for t in rule["targets"] or []
                if t["type"] == "schedule_reference"
            ]
            rules.append(
                _Rule(
                    index=idx,
                    target_names=tuple(names),
                    target_ids=tuple(targets),
                )
            )

        return cls(
            ep_id=resp["id"],
            name=resp["name"],
            html_url=resp["html_url"],
            rules=rules,
        )

    def as_dict(self) -> dict[str, Any]:
        """Render object as dictionary."""
        return dataclasses.asdict(self)
