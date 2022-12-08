"""
Poll PagerDuty and identify on-call coverage gaps.
"""
from __future__ import annotations

import logging
from typing import Any

from pd_utils.model import EscalationRuleCoverage as EscCoverage
from pd_utils.model import ScheduleCoverage as SchCoverage
from pd_utils.util import datetool
from pd_utils.util import ioutil
from pd_utils.util import PagerDutyAPI


class CoverageGapReport:
    """Poll all schedules in an instance and identify coverage gaps."""

    log = logging.getLogger()
    base_url = "https://api.pagerduty.com"

    def __init__(
        self,
        pagerduty_connection: PagerDutyAPI,
        *,
        max_query_limit: int = 100,
        look_ahead_days: int = 14,
    ) -> None:
        """
        Args:
            pagerduty_connection: PagerDutyAPI object
            max_query_limit: Number of objects to request at once from PD (max: 100)
            look_ahead_days: Number of days to look ahead on schedule (default: 14)
        """
        self._since = datetool.utcnow_isotime()
        self._until = datetool.add_offset(self._since, days=look_ahead_days)
        self._max_query_limit = max_query_limit
        self._schedule_map: dict[str, SchCoverage] = {}
        self._escalation_map: dict[str, EscCoverage] = {}

        self._query = pagerduty_connection

    def run_reports(self) -> tuple[str, str]:
        """
        Runs reports. Returns csv strings of Schedule and Escalation reports.

        Raises:
            QueryError
        """
        self._map_schedule_coverages(self._get_all_schedule_ids())
        self._map_escalation_coverages(self._get_all_escalations())
        self._hydrate_escalation_coverage_flags()

        schedule = ioutil.to_csv_string(list(self._schedule_map.values()))
        escalation = ioutil.to_csv_string(list(self._escalation_map.values()))
        return schedule, escalation

    def get_schedule_coverage(self, schedule_id: str) -> SchCoverage | None:
        """Get ScheduleCoverage from PagerDuty with specific schedule id."""
        schobj: SchCoverage | None = None
        params = {
            "since": self._since,
            "until": self._until,
            "time_zone": "Etc/UTC",
        }
        result = self._query.get(f"/schedules/{schedule_id}", params=params)

        if result:
            schobj = SchCoverage.build_from(result)
        else:
            self.log.error("Error fetching schedule %s", schedule_id)

        return schobj

    def _get_all_escalations(self) -> list[dict[str, Any]]:
        """Pull all escalation polcies from PagerDuty."""
        self._query.set_query_target("/escalation_policies", "escalation_policies")
        self._query.set_query_params({})

        eps = [ep for ep in self._query.query_iter(self._max_query_limit)]

        self.log.info("Discovered %d escalation policies.", len(eps))
        return eps

    def _get_all_schedule_ids(self) -> set[str]:
        """Get all unique schedule IDs."""
        self._query.set_query_target("/schedules", "schedules")
        self._query.set_query_params({})

        sch_ids = [sch["id"] for sch in self._query.query_iter(self._max_query_limit)]

        self.log.info("Discovered %d schedules.", len(sch_ids))
        return set(sch_ids)

    def _map_schedule_coverages(self, schedule_ids: set[str]) -> None:
        """Map scheduleId:ScheduleCoverage object, pulling detailed object from PD."""
        self.log.info("Pulling %d schedules for coverage.", len(schedule_ids))

        for idx, sch_id in enumerate(schedule_ids, 1):
            self.log.debug("Pulling %s (%d of %d)", sch_id, idx, len(schedule_ids))

            coverage = self.get_schedule_coverage(sch_id)
            self._schedule_map.update({sch_id: coverage} if coverage else {})

    def _map_escalation_coverages(self, escalations: list[dict[str, Any]]) -> None:
        """Map scheduleId:EscCoverage object, from pulled escalations."""
        self.log.info("Mapping %d escalations for coverage", len(escalations))

        for escalation in escalations:
            ep_coverage = EscCoverage.build_from(escalation)
            rule_map = {f"{ep.policy_id}-{ep.rule_index}": ep for ep in ep_coverage}
            self._escalation_map.update(rule_map)

        self.log.info("%d total objects converted", len(self._escalation_map))

    def _hydrate_escalation_coverage_flags(self) -> None:
        """Test all mapped escalations and set each `has_gap` flag for rules."""
        # NOTE: Schedules should be mapped before this is called

        for ep_rule in self._escalation_map.values():
            times = self._extract_entries(ep_rule.rule_target_ids)
            ep_rule.is_fully_covered = datetool.is_covered(
                time_slots=times,
                range_start=self._since,
                range_stop=self._until,
            )

    def _extract_entries(self, sch_ids: tuple[str, ...]) -> list[tuple[str, str]]:
        """Extract all timestamp entries from given schedules"""
        entries: list[tuple[str, str]] = []
        schedules = [self._schedule_map[k] for k in sch_ids if k in self._schedule_map]
        for schedule in schedules:
            entries.extend(list(schedule.entries))
        return entries
