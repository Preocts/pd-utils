from __future__ import annotations

import json
from pathlib import Path

from pd_utils.model import UserReportRow

USER = Path("tests/fixture/user_report/user.json").read_text()


def test_model() -> None:
    resp = json.loads(USER)

    model = UserReportRow.build_from(resp)

    assert model.id == "PSIUGWW"
    assert model.name == "Preocts"
    assert model.email == "preocts@preocts.com"
    assert model.html_url == "https://preocts.pagerduty.com/users/PSIUGWW"
    assert model.title == "Software Engineer"
    assert model.base_role == "user"
    assert model.timezone == "America/New_York"
    assert model.observer_in == []
    assert model.responder_in == []
    assert model.manager_in == []
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


def test_model_no_teams() -> None:
    resp = json.loads(USER)
    resp["teams"] = None

    model = UserReportRow.build_from(resp)

    assert model.manager_in == []


def test_model_no_contact_methods() -> None:
    resp = json.loads(USER)
    resp["contact_methods"] = None

    model = UserReportRow.build_from(resp)

    assert model.has_email is False


def test_model_no_notificatoin_rules() -> None:
    resp = json.loads(USER)
    resp["notification_rules"] = None

    model = UserReportRow.build_from(resp)

    assert model.high_urgency_email_delay is None
