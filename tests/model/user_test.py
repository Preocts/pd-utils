from __future__ import annotations

import json
from pathlib import Path

from pd_utils.model import User

USER = Path("tests/fixture/user_report/user.json").read_text()


def test_model() -> None:
    resp = json.loads(USER)

    model = User.build_from(resp)

    assert model.name == "Preocts"
    assert model.email == "preocts@preocts.com"
    assert model.html_url == "https://preocts.pagerduty.com/users/PSIUGWW"
    assert model.title == "Software Engineer"
    assert model.base_role == "user"
    assert model.timezone == "America/New_York"
    assert model.observer_in is None
    assert model.responder_in == ["Egg Carton"]
    assert model.manager_in == ["Eggmins"]
    assert model.has_email is True
    assert model.has_push is False
    assert model.has_sms is True
    assert model.has_phone is True
    assert model.has_blocked is True
    assert model.high_urgency_email_delay == ["0"]
    assert model.high_urgency_push_delay is None
    assert model.high_urgency_phone_delay == ["2", "4"]
    assert model.high_urgency_sms_delay == ["0"]
    assert model.low_urgency_email_delay == ["0"]
    assert model.low_urgency_push_delay is None
    assert model.low_urgency_phone_delay is None
    assert model.low_urgency_sms_delay == ["5"]
