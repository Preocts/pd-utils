from __future__ import annotations

import json
from pathlib import Path

from pd_utils.model import Incident

SCHEDULE = Path("tests/fixture/close-incidents/incidents.json").read_text()


def test_model() -> None:
    resp = json.loads(SCHEDULE)[0]["incidents"][0]

    model = Incident.build_from(resp)
    dct = model.as_dict()

    assert dct["incident_id"] == "Q36LM3UBN4V94O"
    assert model.incident_number == 3
    assert model.title == "This has no priority"
    assert model.created_at == "2022-08-01T02:38:25Z"
    assert model.status == "acknowledged"
    assert model.last_status_change_at == "2022-08-01T02:39:15Z"
    assert model.has_priority is False
    assert model.urgency == "high"
