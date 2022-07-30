"""Model escalation policy gap coverage."""
from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class EscalationRuleCoverage:
    policy_id: str
    policy_name: str
    policy_html_url: str
    rule_index: int
    rule_target_names: tuple[str, ...]
    rule_target_ids: tuple[str, ...]
    is_fully_covered: bool | None = None

    @classmethod
    def build_from(cls, resp: dict[str, Any]) -> list[EscalationRuleCoverage]:
        """Build objects from PagerDuty escalation_policies response."""
        rules: list[EscalationRuleCoverage] = []
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
                cls(
                    policy_id=resp["id"],
                    policy_name=resp["name"],
                    policy_html_url=resp["html_url"],
                    rule_index=idx,
                    rule_target_names=tuple(names),
                    rule_target_ids=tuple(targets),
                )
            )
        return rules

    def as_dict(self) -> dict[str, Any]:
        """Render object as dictionary."""
        return dataclasses.asdict(self)
