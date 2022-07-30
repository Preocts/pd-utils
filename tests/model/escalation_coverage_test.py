from __future__ import annotations

import json
from pathlib import Path

from pd_utils.model import EscalationCoverage

EP_POLICIES = Path("tests/fixture/cov_gap/ep_list.json").read_text()


def test_model() -> None:
    resp = json.loads(EP_POLICIES)[0]["escalation_policies"][0]

    model = EscalationCoverage.build_from(resp)
    dct = model.as_dict()

    assert model.name == "Mind the gap"
    assert len(model.rules) == 4
    assert model.rules[0].target_ids == ("PQ1AJP1", "PA82FR2")
    assert dct["ep_id"] == "P46S1RA"
    assert len(dct["rules"]) == 4
