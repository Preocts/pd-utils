from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import Response

from pd_utils.close_old_incidents import CloseOldIncidents
from pd_utils.close_old_incidents import QueryError
from pd_utils.model import Incident
from pd_utils.util import DateTool


INCIDENTS_RESP = Path("tests/fixture/close-incidents/incidents.json").read_text()
EXPECTED_IDS = {"Q36LM3UBN4V94O", "Q3YH44AL350A23"}

LOG_ENTRIES_RESP = Path("tests/fixture/close-incidents/logentry.json").read_text()
EXPECTED_LOG_ID = "R15HMGZ64N39C61067KAZ68JIN"


@pytest.fixture
def closer() -> CloseOldIncidents:
    return CloseOldIncidents("mock", "mock")


@pytest.fixture
def mock_incidents() -> list[Incident]:
    now = DateTool.utcnow_isotime()
    days5 = DateTool.add_offset(now, days=5)
    days10 = DateTool.add_offset(now, days=9, minutes=58)
    old = DateTool.add_offset(now, days=10, minutes=1)
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