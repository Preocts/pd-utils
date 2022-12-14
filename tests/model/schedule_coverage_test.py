from __future__ import annotations

import json
from pathlib import Path

from pd_utils.model import ScheduleCoverage

SCHEDULE = Path("tests/fixture/cov_gap/schedule_gap.json").read_text()


def test_model() -> None:
    resp = json.loads(SCHEDULE)

    model = ScheduleCoverage.build_from(resp)

    assert model.coverage == 97.9
    assert model.name == "Preocts Coverage Gaps"
    assert model.pd_id == "PG3MDI8"
    assert len(model.entries) == 15
