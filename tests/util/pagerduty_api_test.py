from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from httpx import Response

from pd_utils.util import PagerDutyAPI

INCIDENTS_RESP = Path("tests/fixture/close-incidents/incidents.json").read_text()
EXPECTED_IDS = {"Q36LM3UBN4V94O", "Q3YH44AL350A23"}


@pytest.fixture
def pdapi() -> PagerDutyAPI:
    return PagerDutyAPI("mock", "mock")


def test_unset_property_object_name_raises(pdapi: PagerDutyAPI) -> None:
    with pytest.raises(ValueError):
        pdapi.object_name


def test_unset_property_route_raises(pdapi: PagerDutyAPI) -> None:
    with pytest.raises(ValueError):
        pdapi.route


def test_set_query_params(pdapi: PagerDutyAPI) -> None:
    params = {"status[]": ["triggered", "resolved"]}
    pdapi.set_query_params(params)

    assert pdapi._params == params


def test_set_query_target(pdapi: PagerDutyAPI) -> None:
    pdapi.set_query_target("/schedules", "schedules")

    assert pdapi.route == "/schedules"
    assert pdapi.object_name == "schedules"


def test_set_query_target_invalid(pdapi: PagerDutyAPI) -> None:
    with pytest.raises(ValueError):
        pdapi.set_query_target("schedules", "schedules")


def test_run_success(pdapi: PagerDutyAPI) -> None:
    resps = json.loads(INCIDENTS_RESP)
    resp = [Response(200, content=json.dumps(resps[0]))]
    pdapi.set_query_target("/incidents", "incidents")

    with patch.object(pdapi._http, "get", side_effect=resp):
        result, more, count = pdapi._query()

    assert more is True
    assert count == 0
    assert result[0]["id"] in EXPECTED_IDS


def test_run_failure(pdapi: PagerDutyAPI) -> None:
    resp = [Response(400, content="")]
    pdapi.set_query_target("/incidents", "incidents")

    with patch.object(pdapi._http, "get", side_effect=resp):
        with pytest.raises(pdapi.QueryError):
            pdapi._query()


def test_run_iter(pdapi: PagerDutyAPI) -> None:
    resps = json.loads(INCIDENTS_RESP)
    resp = [Response(200, content=json.dumps(r)) for r in resps]
    pdapi.set_query_target("/incidents", "incidents")
    results = []

    with patch.object(pdapi._http, "get", side_effect=resp):

        for result in pdapi.query_iter(limit=1):
            results.append(result)

    assert not {r["id"] for r in results} - EXPECTED_IDS


def test_get_success(pdapi: PagerDutyAPI) -> None:
    resp = Response(200, content='{"test": "pass"}')
    with patch.object(pdapi._http, "get", return_value=resp) as mock:
        result = pdapi.get("/incidents", {"param1": None, "param2": "Hi"})
        kwargs = mock.call_args.kwargs

    assert result
    assert result["test"] == "pass"
    assert kwargs["params"] == {"param2": "Hi"}


def test_get_failure(pdapi: PagerDutyAPI) -> None:
    resp = Response(400)
    with patch.object(pdapi._http, "get", return_value=resp):
        result = pdapi.get("/incidents")

    assert result is None


@pytest.mark.parametrize(
    ("content", "expected", "status"),
    (
        ('{"test": "pass"}', {"test": "pass"}, 200),
        ("test pass", "test pass", 200),
        (None, None, 200),
        ('{"test": "pass"}', None, 400),
        ("test pass", None, 400),
        (None, None, 400),
    ),
)
def test_put_success(
    pdapi: PagerDutyAPI,
    content: str | None,
    expected: str | dict[str, Any] | None,
    status: int,
) -> None:
    resp = Response(status, content=content)
    with patch.object(pdapi._http, "put", return_value=resp) as mock:
        result = pdapi.put("/incidents", {"param1": None, "param2": "Hi"})
        kwargs = mock.call_args.kwargs

    assert result == expected
    assert kwargs["json"] == {"param1": None, "param2": "Hi"}


def test_put_failure(pdapi: PagerDutyAPI) -> None:
    resp = Response(400)
    with patch.object(pdapi._http, "put", return_value=resp):
        result = pdapi.put("/incidents")

    assert result is None
