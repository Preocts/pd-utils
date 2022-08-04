from __future__ import annotations

import pytest

from pd_utils.util import PagerDutyQuery

# from unittest.mock import patch


@pytest.fixture
def query() -> PagerDutyQuery:
    return PagerDutyQuery("mock", "mock")


def test_unset_property_object_name_raises(query: PagerDutyQuery) -> None:
    with pytest.raises(ValueError):
        query.object_name


def test_unset_property_route_raises(query: PagerDutyQuery) -> None:
    with pytest.raises(ValueError):
        query.route


def test_set_query_fields(query: PagerDutyQuery) -> None:
    fields = {"status[]": ["triggered", "resolved"]}
    query.set_query_fields(fields)

    assert query._fields == fields


def test_set_query_target(query: PagerDutyQuery) -> None:
    query.set_query_target("/schedules", "schedules")

    assert query.route == "/schedules"
    assert query.object_name == "schedules"


def test_set_query_target_invalid(query: PagerDutyQuery) -> None:
    with pytest.raises(ValueError):
        query.set_query_target("schedules", "schedules")
