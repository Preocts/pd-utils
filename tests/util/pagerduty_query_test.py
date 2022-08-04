from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import Response

from pd_utils.util import PagerDutyQuery

INCIDENTS_RESP = Path("tests/fixture/close-incidents/incidents.json").read_text()
EXPECTED_IDS = {"Q36LM3UBN4V94O", "Q3YH44AL350A23"}


@pytest.fixture
def query() -> PagerDutyQuery:
    return PagerDutyQuery("mock", "mock")


def test_unset_property_object_name_raises(query: PagerDutyQuery) -> None:
    with pytest.raises(ValueError):
        query.object_name


def test_unset_property_route_raises(query: PagerDutyQuery) -> None:
    with pytest.raises(ValueError):
        query.route


def test_set_query_params(query: PagerDutyQuery) -> None:
    params = {"status[]": ["triggered", "resolved"]}
    query.set_query_params(params)

    assert query._params == params


def test_set_query_target(query: PagerDutyQuery) -> None:
    query.set_query_target("/schedules", "schedules")

    assert query.route == "/schedules"
    assert query.object_name == "schedules"


def test_set_query_target_invalid(query: PagerDutyQuery) -> None:
    with pytest.raises(ValueError):
        query.set_query_target("schedules", "schedules")


def test_run_success(query: PagerDutyQuery) -> None:
    resps = json.loads(INCIDENTS_RESP)
    resp = [Response(200, content=json.dumps(resps[0]))]
    query.set_query_target("/incidents", "incidents")

    with patch.object(query._http, "get", side_effect=resp):
        result, more, count = query.run()

    assert more is True
    assert count == 0
    assert result[0]["id"] in EXPECTED_IDS


def test_run_failure(query: PagerDutyQuery) -> None:
    resp = [Response(400, content="")]
    query.set_query_target("/incidents", "incidents")

    with patch.object(query._http, "get", side_effect=resp):
        with pytest.raises(query.QueryError):
            query.run()


def test_run_iter(query: PagerDutyQuery) -> None:
    resps = json.loads(INCIDENTS_RESP)
    resp = [Response(200, content=json.dumps(r)) for r in resps]
    query.set_query_target("/incidents", "incidents")
    results = []

    with patch.object(query._http, "get", side_effect=resp):

        for result in query.run_iter(limit=1):
            results.extend(result)

    assert not {r["id"] for r in results} - EXPECTED_IDS
