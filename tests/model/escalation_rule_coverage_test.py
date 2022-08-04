from __future__ import annotations

import json
from pathlib import Path

from pd_utils.model import EscalationRuleCoverage

EP_POLICIES = Path("tests/fixture/cov_gap/ep_list.json").read_text()


def test_model() -> None:
    resp = json.loads(EP_POLICIES)[0]["escalation_policies"][0]

    models = EscalationRuleCoverage.build_from(resp)

    assert models[0].policy_name == "Mind the gap"
    assert len(models) == 4
    assert models[0].rule_target_ids == ("PQ1AJP1", "PA82FR2")
