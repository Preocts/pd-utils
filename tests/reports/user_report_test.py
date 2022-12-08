from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pd_utils.model import UserReportRow
from pd_utils.model import UserTeam
from pd_utils.report.user_report import _Team
from pd_utils.report.user_report import UserReport
from pd_utils.util.pagerduty_api import PagerDutyAPI

USER = Path("tests/fixture/user_report/user.json").read_text()
MEMBERS = Path("tests/fixture/user_report/members.json").read_text()
EXPECTED_TEAMS = {
    _Team("Egg Carton", "PLNRGGS"),
    _Team("Eggmins", "PHB3G42"),
}
SCHEDULES = Path("tests/fixture/user_report/schedules.json").read_text()
EXPECTED_USERS = {"PSIUGWW", "PSIUGWX"}


@pytest.fixture
def report() -> UserReport:
    return UserReport(PagerDutyAPI("", "", 1))


def test_run_report(report: UserReport) -> None:
    with patch.object(report, "_get_users_and_teams", return_value=(dict(), set())):
        with patch.object(report, "_get_users_on_schedules", return_value=set()):
            result = report.run_report()

    assert result == ""


@pytest.mark.parametrize(
    ("teams", "expected"),
    (
        (json.loads(USER)["teams"], EXPECTED_TEAMS),
        (None, set()),
    ),
)
def test_extract_team_ids(
    report: UserReport,
    teams: list[dict[str, Any]] | None,
    expected: set[str],
) -> None:
    result = report._extract_teams(teams)

    assert result == expected


@pytest.mark.parametrize(
    ("users", "expected_len"),
    (
        ([json.loads(USER)], 1),
        ([], 0),
    ),
)
def test_get_users_and_teams(
    report: UserReport,
    users: list[dict[str, Any]],
    expected_len: int,
) -> None:
    with patch.object(report._query, "query_iter", return_value=users):
        user_map, teams = report._get_users_and_teams()

    assert len(user_map) == expected_len


def test_get_team_memberships(report: UserReport) -> None:
    resp = [json.loads(MEMBERS)]

    with patch.object(report._query, "query_iter", return_value=resp):

        result = report._get_team_memberships(EXPECTED_TEAMS)
    print(result)
    assert len(result) == len(EXPECTED_TEAMS)


def test_hydrate_team_membership(report: UserReport) -> None:
    mock_map = {"PSIUGWW": UserReportRow.build_from(json.loads(USER))}
    mock_teams = [
        UserTeam("PSIUGWW", "PLNRGGS", "Egg Carton", "responder"),
        UserTeam("PSIUGWW", "PLNRGGS", "Eggmins", "responder"),
        UserTeam("PSIUGWW", "PLNRGGS", "Bonus Hunt", "observer"),
    ]

    report._hydrate_team_membership(mock_map, mock_teams)

    assert mock_map["PSIUGWW"].responder_in
    assert mock_map["PSIUGWW"].observer_in
    assert mock_map["PSIUGWW"].manager_in is None
    assert "Egg Carton, PLNRGGS" in mock_map["PSIUGWW"].responder_in
    assert "Eggmins, PLNRGGS" in mock_map["PSIUGWW"].responder_in
    assert "Bonus Hunt, PLNRGGS" in mock_map["PSIUGWW"].observer_in


def test_get_users_on_schedules(report: UserReport) -> None:
    resp = json.loads(SCHEDULES)["schedules"]

    with patch.object(report._query, "query_iter", return_value=resp):
        result = report._get_users_on_schedules()

    assert result == EXPECTED_USERS


def test_hydrate_on_schedule_flag(report: UserReport) -> None:
    mock_map = {
        "PSIUGWW": UserReportRow.build_from(json.loads(USER)),
        "PSIUGWX": UserReportRow.build_from(json.loads(USER)),
    }
    mock_scheduled = {"PSIUGWW", "PSIUGXX"}

    report._hydrate_on_schedule_flag(mock_map, mock_scheduled)

    assert mock_map["PSIUGWW"].on_schedule is True
    assert mock_map["PSIUGWX"].on_schedule is False
