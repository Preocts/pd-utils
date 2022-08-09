from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from httpx import Response

from pd_utils.model import Incident
from pd_utils.tool import close_old_incidents
from pd_utils.tool.close_old_incidents import CloseOldIncidents
from pd_utils.util import DateTool

INCIDENTS_RESP = Path("tests/fixture/close-incidents/incidents.json").read_text()
EXPECTED_IDS = {"Q36LM3UBN4V94O", "Q3YH44AL350A23"}

LOG_ENTRIES_RESP = Path("tests/fixture/close-incidents/logentry.json").read_text()
EXPECTED_LOG_ID = "R15HMGZ64N39C61067KAZ68JIN"

# Built from the mock objects in fixture mock_incidents()
MOCK_REPORT = "\n".join(
    [
        "incident_id,incident_number,title,created_at,status,last_status_change_at,has_priority,urgency",  # noqa: E501
        "a,1,New,2022-08-02T02:33:35Z,triggered,2022-08-02T02:33:35Z,True,high",
        "b,4,Old,2022-08-12T02:34:35Z,triggered,2022-08-12T02:34:35Z,False,high",
        "c,2,Mid,2022-08-07T02:33:35Z,acknowledged,2022-08-07T02:33:35Z,True,low",
        "d,3,Cusp,2022-08-11T03:31:35Z,acknowledged,2022-08-11T03:31:35Z,False,low",
    ]
)


@pytest.fixture
def closer() -> CloseOldIncidents:
    return CloseOldIncidents("mock", "mock")


@pytest.fixture
def mock_incidents() -> list[Incident]:
    now = DateTool.utcnow_isotime()
    days5 = DateTool.add_offset(now, days=-5)
    days10 = DateTool.add_offset(now, days=-9, minutes=-58)
    old = DateTool.add_offset(now, days=-10, minutes=-1)
    incs = [
        Incident("a", 1, "New", now, "triggered", now, True, "high"),
        Incident("b", 4, "Old", old, "triggered", old, False, "high"),
        Incident("c", 2, "Mid", days5, "acknowledged", days5, True, "low"),
        Incident("d", 3, "Cusp", days10, "acknowledged", days10, False, "low"),
    ]

    return incs


def test_get_newest_log_entry(closer: CloseOldIncidents) -> None:
    mock_resp = json.loads(LOG_ENTRIES_RESP)["log_entries"][0]
    resp = [([mock_resp], None, None)]

    with patch.object(closer._query, "run", side_effect=resp) as mockrun:

        results = closer._get_newest_log_entry("mock")

    assert mockrun.call_count == 1
    assert results["id"] == EXPECTED_LOG_ID


def test_get_all_incidents(closer: CloseOldIncidents) -> None:
    resps = json.loads(INCIDENTS_RESP)
    resp_gen = (r["incidents"][0] for r in resps)

    with patch.object(closer._query, "run_iter", return_value=resp_gen):

        results = closer._get_all_incidents()

    assert not {i.incident_id for i in results} - EXPECTED_IDS


def test_isolate_old_incidents(
    closer: CloseOldIncidents,
    mock_incidents: list[Incident],
) -> None:
    results = closer._isolate_old_incidents(mock_incidents)

    assert len(results) == 1
    assert results[0].incident_number == 4


def test_isolate_nonpriority_incidents(
    closer: CloseOldIncidents,
    mock_incidents: list[Incident],
) -> None:
    results = closer._isolate_nonpriority_incidents(mock_incidents)

    assert len(results) == 2
    assert results[0].has_priority is False


def test_isolate_inactive_incidents(
    closer: CloseOldIncidents,
    mock_incidents: list[Incident],
) -> None:
    mocklog = json.loads(LOG_ENTRIES_RESP)["log_entries"][0]
    mocklogs: list[dict[str, Any]] = []
    for inc in mock_incidents:
        mocklog["created_at"] = inc.created_at
        mocklogs.append(mocklog.copy())

    with patch.object(closer, "_get_newest_log_entry", side_effect=mocklogs):

        results = closer._isolate_inactive_incidents(mock_incidents)

    assert len(results) == 1
    assert results[0].incident_number == 4


@pytest.mark.parametrize(("status", "expect"), ((200, True), (400, False)))
def test_resolve_incident(status: int, expect: bool, closer: CloseOldIncidents) -> None:
    resps = [Response(status)]
    incident_id = "123"
    title = "This is a test"
    expected_title = f"{close_old_incidents.TITLE_TAG} {title}"
    with patch.object(closer._http, "put", side_effect=resps) as http:

        result = closer._resolve_incident(incident_id, title)
        kwargs = http.call_args.kwargs

    assert incident_id in kwargs["url"]
    assert kwargs["json"]["incident"]["status"] == "resolved"
    assert kwargs["json"]["incident"]["title"] == expected_title
    assert result is expect


def test_close_incidents(
    closer: CloseOldIncidents,
    mock_incidents: list[Incident],
) -> None:
    resps = [
        Response(200),
        Response(400),
        Response(200),
        Response(400),
    ]

    with patch.object(closer._http, "put", side_effect=resps):

        success, error = closer._close_incidents(mock_incidents)

    assert len(success) == 2
    assert len(error) == 2


def test_run_empty_results(closer: CloseOldIncidents) -> None:
    resp_gen = []  # type: ignore
    with patch.object(closer._query, "run_iter", return_value=resp_gen) as http:
        closer.run()

        assert http.call_count == 1


def test_run_empty_ignore_activity(closer: CloseOldIncidents) -> None:
    resp_gen = []  # type: ignore
    closer._close_active = True
    with patch.object(closer._query, "run_iter", return_value=resp_gen):
        with patch.object(closer, "_isolate_inactive_incidents") as avoid:
            closer.run()

            avoid.assert_not_called()


def test_run_empty_file(mock_filename: str, closer: CloseOldIncidents) -> None:
    closer.run(mock_filename)
