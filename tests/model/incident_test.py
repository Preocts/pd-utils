from __future__ import annotations

import json
from pathlib import Path

from pd_utils.model import Incident

SCHEDULE = Path("tests/fixture/close-incidents/incidents.json").read_text()


def test_model() -> None:
    resp = json.loads(SCHEDULE)[0]["incidents"][0]

    model = Incident.build_from(resp)
    dct = model.as_dict()

    assert dct["incident_id"] == "Q28ZYJ9YPJ7XRN"
    assert model.incident_number == 1
    assert model.title == "This is a test"
    assert model.created_at == "2022-07-31T02:36:20Z"
    assert model.status == "resolved"
    assert model.last_status_change_at == "2022-07-31T04:34:44Z"
    assert model.has_priority is False
    assert model.urgency == "high"
