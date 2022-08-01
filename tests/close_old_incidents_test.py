from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import Response

from pd_utils.close_old_incidents import CloseOldIncidents
from pd_utils.close_old_incidents import QueryError


INCIDENTS_RESP = Path("tests/fixture/close-incidents/incidents.json").read_text()
EXPECTED_IDS = {"Q36LM3UBN4V94O", "Q3YH44AL350A23"}

LOG_ENTRIES_RESP = Path("tests/fixture/close-incidents/logentry.json").read_text()
EXPECTED_LOG_ID = "R15HMGZ64N39C61067KAZ68JIN"


@pytest.fixture
def closer() -> CloseOldIncidents:
    return CloseOldIncidents("mock", "mock")


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
