from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from pd_utils import user_report
from pd_utils.model import User
from pd_utils.user_report import UserReport

USER = Path("tests/fixture/user_report/user.json").read_text()


def test_main() -> None:

    with patch.object(user_report.UserReport, "run_report", return_value="") as mock:

        result = user_report.main([])

        assert mock.call_count == 1
        assert result == 0


def test_run_report() -> None:
    resps = [[json.loads(USER)]]

    report = user_report.UserReport("mock")
    with patch.object(report._query, "run_iter", return_value=resps):

        result = report.run_report()

    assert "Preocts" in result


def test_isolate_by_base_role() -> None:
    users = [User.build_from(json.loads(USER))]

    hit = UserReport._isolate_by_base_role(users, ["user", "admin"])
    miss = UserReport._isolate_by_base_role(users, ["read_only_user", "admin"])
    empty = UserReport._isolate_by_base_role(users, [])

    assert hit == users
    assert miss == []
    assert empty == users


def test_isolate_by_team_role() -> None:
    users = [User.build_from(json.loads(USER))]

    hit = UserReport._isolate_by_team_role(users, ["manager", "responder"])
    miss = UserReport._isolate_by_team_role(users, ["observer"])
    empty = UserReport._isolate_by_team_role(users, [])

    assert hit == users
    assert miss == []
    assert empty == users
