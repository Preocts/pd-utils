from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from _pytest.monkeypatch import MonkeyPatch
from httpx import Response

from pd_utils import close_old_incidents
from pd_utils.close_old_incidents import CloseOldIncidents
from pd_utils.close_old_incidents import QueryError
from pd_utils.model import Incident
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


def test_get_all_incidents(closer: CloseOldIncidents) -> None:
    resps = json.loads(INCIDENTS_RESP)
    resp = [Response(200, content=json.dumps(r)) for r in resps]

    with patch.object(closer._http, "get", side_effect=resp) as mockhttp:

        results = closer._get_all_incidents()

    assert mockhttp.call_count == 2
    assert not {i.incident_id for i in results} - EXPECTED_IDS


def test_get_all_incidents_error(closer: CloseOldIncidents) -> None:
    resp = [Response(404, content="Not Found")]

    with patch.object(closer._http, "get", side_effect=resp):
        with pytest.raises(QueryError):
            closer._get_all_incidents()


def test_get_newest_log_entry(closer: CloseOldIncidents) -> None:
    resp = [Response(200, content=LOG_ENTRIES_RESP)]

    with patch.object(closer._http, "get", side_effect=resp) as mockhttp:

        results = closer._get_newest_log_entry("mock")

    assert mockhttp.call_count == 1
    assert results["id"] == EXPECTED_LOG_ID


def test_get_newest_log_entry_error(closer: CloseOldIncidents) -> None:
    resp = [Response(404, content="Not Found")]

    with patch.object(closer._http, "get", side_effect=resp):
        with pytest.raises(QueryError):
            closer._get_newest_log_entry("mock")


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


def test_main_no_optional_args() -> None:

    with patch.object(close_old_incidents, "CloseOldIncidents") as mockclass:
        close_old_incidents.main(["--token", "mock", "--email", "mock@mock.com"])
        kwargs = mockclass.call_args.kwargs
        print(mockclass.call_args.kwargs)

    assert kwargs == {
        "token": "mock",
        "email": "mock@mock.com",
        "close_after_days": 10,
        "close_active": False,
        "close_priority": False,
    }


def test_main_optional_args() -> None:

    with patch.object(close_old_incidents, "CloseOldIncidents") as mockclass:
        close_old_incidents.main(
            [
                "--token",
                "mock",
                "--email",
                "mock@mock.com",
                "--close-active",
                "--close-priority",
                "--close-after-days=5",
            ]
        )
        kwargs = mockclass.call_args.kwargs

    assert kwargs == {
        "token": "mock",
        "email": "mock@mock.com",
        "close_after_days": 5,
        "close_active": True,
        "close_priority": True,
    }


def test_save_file(
    mock_incidents: list[Incident],
    monkeypatch: MonkeyPatch,
) -> None:
    now = datetime.datetime(1999, 12, 25, 13, 50, 30, 0)
    mock_dt = MagicMock(now=MagicMock(return_value=now))
    monkeypatch.setattr(close_old_incidents.datetime, "datetime", mock_dt)
    mock_filename = "temp_save_test"
    filecheck = Path(f"{mock_filename}-{now.strftime('%Y%m%d-%H%M')}.csv")
    client = close_old_incidents.CloseOldIncidents("mock", "mock")

    try:
        client._write_file(mock_incidents, mock_filename)

        assert filecheck.exists()

    finally:
        filecheck.unlink(True)


def test_empty_save(monkeypatch: MonkeyPatch) -> None:
    now = datetime.datetime(1999, 12, 25, 13, 50, 30, 0)
    mock_dt = MagicMock(now=MagicMock(return_value=now))
    monkeypatch.setattr(close_old_incidents.datetime, "datetime", mock_dt)
    mock_filename = "temp_save_test"
    filecheck = Path(f"{mock_filename}-{now.strftime('%Y%m%d-%H%M')}.csv")
    client = close_old_incidents.CloseOldIncidents("mock", "mock")

    try:
        client._write_file([], mock_filename)

        assert not filecheck.exists()

    finally:
        filecheck.unlink(True)


def test_load_file(closer: CloseOldIncidents) -> None:
    writefile = Path("temp_load_test.csv")
    with writefile.open("w") as outfile:
        outfile.write(MOCK_REPORT)

    try:
        result = closer._load_input_file(str(writefile))

        assert len(result) == 4

    finally:
        writefile.unlink(True)


def test_run_empty_results(closer: CloseOldIncidents) -> None:
    resp = Response(200, content='{"incidents": [], "more": false}')
    with patch.object(closer._http, "get", return_value=resp):
        closer.run()


def test_run_empty_file(closer: CloseOldIncidents) -> None:
    with patch.object(closer, "_load_input_file", return_value=[]) as mocked:
        closer.run("mock_file")

        assert mocked.call_count == 1
        mocked.assert_called_with("mock_file")


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
