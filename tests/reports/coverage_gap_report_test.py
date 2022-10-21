from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from pd_utils.model import ScheduleCoverage
from pd_utils.model.escalation_rule_coverage import EscalationRuleCoverage
from pd_utils.report.coverage_gap_report import CoverageGapReport

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
            has_direct_contact=False,
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
            has_direct_contact=False,
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
            has_direct_contact=False,
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


def test_get_schedule_coverage(search: CoverageGapReport) -> None:
    with patch.object(search._query, "get", return_value=json.loads(SCHEDULE_RESP)):

        result = search.get_schedule_coverage("mock")

    assert result is not None
    assert result.pd_id == EXPECTED_ID


def test_get_schedule_coverage_fails(search: CoverageGapReport) -> None:
    with patch.object(search._query, "get", return_value=None):

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


def test_run_clean_exits_no_work(search: CoverageGapReport) -> None:
    resp_gen = []  # type: ignore

    with patch.object(search._query, "query_iter", return_value=resp_gen):
        search.run_reports()
