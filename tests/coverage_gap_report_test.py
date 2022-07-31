from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import Response

from pd_utils import coverage_gap_report
from pd_utils.coverage_gap_report import CoverageGapReport
from pd_utils.coverage_gap_report import QueryError
from pd_utils.model import ScheduleCoverage
from pd_utils.model.escalation_rule_coverage import EscalationRuleCoverage

SCHEDULES_RESP = Path("tests/fixture/cov_gap/schedule_list.json").read_text()
EXPECTED_IDS = {"PG3MDI8", "P4TPEME"}

SCHEDULE_RESP = Path("tests/fixture/cov_gap/schedule_gap.json").read_text()
EXPECTED_ID = "PG3MDI8"

EP_RESP = Path("tests/fixture/cov_gap/ep_list.json").read_text()
EP_EXPECTED_COUNT = 2


@pytest.fixture
def search() -> CoverageGapReport:
    return CoverageGapReport("mock", max_query_limit=1, look_ahead_days=14)


@pytest.fixture
def mapped_search(search: CoverageGapReport) -> CoverageGapReport:
    search._escalation_map = {
        # Expected to have gaps in coverage
        "mock1": EscalationRuleCoverage(
            policy_name="Mind the gap",
            policy_id="P46S1RA",
            policy_html_url="https://preocts.pagerduty.com/escalation_policies/P46S1RA",
            rule_index=1,
            rule_target_names=("Morning shift", "Late shift gap"),
            rule_target_ids=("sch1", "sch2"),
            is_fully_covered=None,
        ),
        # Expected to be fully covered
        "mock2": EscalationRuleCoverage(
            policy_id="P46S1RA",
            policy_name="No gap",
            policy_html_url="https://preocts.pagerduty.com/escalation_policies/P46S1RA",
            rule_index=1,
            rule_target_names=("Morning shift", "Late shift"),
            rule_target_ids=("sch1", "sch3"),
            is_fully_covered=None,
        ),
        # Expected to have gap in range
        "mock3": EscalationRuleCoverage(
            policy_id="P46S1RA",
            policy_name="No gap",
            policy_html_url="https://preocts.pagerduty.com/escalation_policies/P46S1RA",
            rule_index=1,
            rule_target_names=("Morning shift", "Late Shorted"),
            rule_target_ids=("sch1", "sch4"),
            is_fully_covered=None,
        ),
    }
    search._schedule_map = {
        "sch1": ScheduleCoverage(
            "sc1",
            "Mornings",
            "...",
            56.3,
            (
                ("2022-07-29T04:18:19Z", "2022-07-29T12:00:00Z"),
                ("2022-07-30T00:00:00Z", "2022-07-30T12:00:00Z"),
                ("2022-07-31T00:00:00Z", "2022-07-31T12:00:00Z"),
            ),
        ),
        "sch2": ScheduleCoverage(
            "sc2",
            "Late shift gap",
            "...",
            56.3,
            (
                ("2022-07-29T04:18:19Z", "2022-07-30T00:00:00Z"),
                ("2022-07-30T12:30:00Z", "2022-07-31T00:00:00Z"),
                ("2022-07-31T12:30:00Z", "2022-08-01T00:00:00Z"),
            ),
        ),
        "sch3": ScheduleCoverage(
            "sc3",
            "Late shift",
            "...",
            56.3,
            (
                ("2022-07-29T04:18:19Z", "2022-07-30T00:00:00Z"),
                ("2022-07-30T12:00:00Z", "2022-07-31T00:00:00Z"),
                ("2022-07-31T12:00:00Z", "2022-08-01T00:00:00Z"),
            ),
        ),
        "sch4": ScheduleCoverage(
            "sc4",
            "Late shift",
            "...",
            56.3,
            (
                ("2022-07-29T04:18:19Z", "2022-07-30T00:00:00Z"),
                ("2022-07-30T12:00:00Z", "2022-07-31T00:00:00Z"),
                ("2022-07-31T12:00:00Z", "2022-07-31T23:00:00Z"),
            ),
        ),
    }
    search._since = "2022-07-29T04:18:19Z"
    search._until = "2022-08-01T00:00:00Z"

    return search


def test_get_all_schedule_ids(search: CoverageGapReport) -> None:
    resp_jsons = json.loads(SCHEDULES_RESP)
    resps = [Response(200, content=json.dumps(resp)) for resp in resp_jsons]
    with patch.object(search._http, "get", side_effect=resps):

        results = search._get_all_schedule_ids()

    assert not results - EXPECTED_IDS


def test_get_all_escalations(search: CoverageGapReport) -> None:
    resp_jsons = json.loads(EP_RESP)
    resps = [Response(200, content=json.dumps(resp)) for resp in resp_jsons]
    with patch.object(search._http, "get", side_effect=resps):

        results = search._get_all_escalations()

    assert len(results) == EP_EXPECTED_COUNT


def test_get_all_schedules_error(search: CoverageGapReport) -> None:
    resps = [Response(401, content="")]

    with patch.object(search._http, "get", side_effect=resps):

        with pytest.raises(QueryError):

            search._get_all_schedule_ids()


def test_get_all_escalations_error(search: CoverageGapReport) -> None:
    resps = [Response(401, content="")]

    with patch.object(search._http, "get", side_effect=resps):

        with pytest.raises(QueryError):

            search._get_all_escalations()


def test_get_schedule_coverage(search: CoverageGapReport) -> None:
    resps = [Response(200, content=SCHEDULE_RESP)]
    with patch.object(search._http, "get", side_effect=resps):

        result = search.get_schedule_coverage("mock")

    assert result is not None
    assert result.pd_id == EXPECTED_ID


def test_get_schedule_coverage_fails(search: CoverageGapReport) -> None:
    resps = [Response(401, content="Failure")]
    with patch.object(search._http, "get", side_effect=resps):

        result = search.get_schedule_coverage("mock")

    assert result is None


def test_map_schedule_coverages(search: CoverageGapReport) -> None:
    mock_ids = ["a", "b", "c"]
    resps = ["Good", "Better", None]

    with patch.object(search, "get_schedule_coverage", side_effect=resps):

        search._map_schedule_coverages(mock_ids)  # type: ignore

    assert len(search._schedule_map) == 2
    assert "c" not in search._schedule_map


def test_map_escalation_coverages(search: CoverageGapReport) -> None:
    mock_eps = json.loads(EP_RESP)[0]["escalation_policies"]

    search._map_escalation_coverages(mock_eps)

    assert len(search._escalation_map) == 4


def test_hydrate_escalation_coverage_flags(mapped_search: CoverageGapReport) -> None:
    mapped_search._hydrate_escalation_coverage_flags()

    assert mapped_search._escalation_map["mock1"].is_fully_covered is False
    assert mapped_search._escalation_map["mock2"].is_fully_covered is True
    assert mapped_search._escalation_map["mock3"].is_fully_covered is False


def test_save_schedule_report(
    mapped_search: CoverageGapReport,
    mock_filename: str,
) -> None:
    mapped_search._save_schedule_report(mock_filename)

    lines = Path(mock_filename).read_text().split("\n")

    # 4 mock schedules + header
    assert len([line for line in lines if line]) == 5


def test_save_escalation_report(
    mapped_search: CoverageGapReport,
    mock_filename: str,
) -> None:
    mapped_search._save_escalation_report(mock_filename)

    lines = Path(mock_filename).read_text().split("\n")

    # 3 mock escalations + header
    assert len([line for line in lines if line]) == 4


def test_main():
    with patch.object(coverage_gap_report.CoverageGapReport, "run_reports") as mocked:
        coverage_gap_report.main(_args=[])

        mocked.assert_called_once()


def test_run(search: CoverageGapReport) -> None:
    resps = [
        Response(200, content='{"schedules": [], "more": false}'),
        Response(200, content='{"escalation_policies": [], "more": false}'),
    ]

    with patch.object(search._http, "get", side_effect=resps):
        search.run_reports()
