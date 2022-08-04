"""Model escalation policy gap coverage."""
from __future__ import annotations

import dataclasses
from typing import Any

from pd_utils.model.base import Base


@dataclasses.dataclass
class EscalationRuleCoverage(Base):
    policy_id: str
    policy_name: str
    policy_html_url: str
    rule_index: int
    rule_target_names: tuple[str, ...]
    rule_target_ids: tuple[str, ...]
    has_direct_contact: bool
    is_fully_covered: bool | None = None

    @classmethod
    def build_from(cls, resp: dict[str, Any]) -> list[EscalationRuleCoverage]:
        """Build objects from PagerDuty escalation_policies response."""
        rules: list[EscalationRuleCoverage] = []
        for idx, rule in enumerate(resp["escalation_rules"] or [], 1):
            direct_contact = False
            names: list[str] = []
            targets: list[str] = []
            for target in rule["targets"]:
                if target["type"] == "user_reference":
                    direct_contact = True
                if target["type"] == "schedule_reference":
                    names.append(target["summary"])
                    targets.append(target["id"])
            rules.append(
                cls(
                    policy_id=resp["id"],
                    policy_name=resp["name"],
                    policy_html_url=resp["html_url"],
                    rule_index=idx,
                    rule_target_names=tuple(names),
                    rule_target_ids=tuple(targets),
                    has_direct_contact=direct_contact,
                )
            )
        return rules
