"""
Poll PagerDuty and identify on-call coverage gaps.
"""
from __future__ import annotations

import csv
import logging

import httpx

from pd_util_scripts.model import ScheduleCoverage as Coverage
from pd_util_scripts.util import DateTool
from pd_util_scripts.util import RuntimeInit

runtime = RuntimeInit("schedule-gap-report")
runtime.init_secrets()
runtime.init_logging()


class QueryError(Exception):
    ...


class CoverageGapReport:
    """Poll all schedules in an instance and identify coverage gaps."""

    log = logging.getLogger()
    base_url = "https://api.pagerduty.com"

    def __init__(
        self,
        token: str,
        *,
        max_query_limit: int = 1,
        look_ahead_days: int = 14,
        report_filename: str | None = None,
    ) -> None:
        """
        Required: PagerDuty API v2 token with read access.

        Args:
            max_query_limit: Number of objects to request at once from PD (max: 100)
            look_ahead_days: Number of days to look ahead on schedule (default: 14)
            report_filename: Defaults to "schedule_gap_reportYYYY-MM-DD.csv"
        """
        self._max_query_limit = max_query_limit
        self._look_ahead_days = look_ahead_days
        self._report_filename = report_filename

        headers = {
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={token}",
        }

        self._http = httpx.Client(headers=headers)

    def run_reports(self) -> None:
        """
        Runs coverage gap reports.

        Raises:
            QueryError
        """
        sch_ids = self._get_all_schedule_ids()

        coverage_map = self._get_schedule_coverages(sch_ids)

        self._save_schedule_report(list(coverage_map.values()))

    def _save_schedule_report(self, coverages: list[Coverage]) -> None:
        """Save report to file."""
        if not self._report_filename:
            now = DateTool.utcnow_isotime().split("T")[0]
            self._report_filename = f"schedule_gap_report{now}.csv"

        self.log.info("Saving %d lines to %s", len(coverages), self._report_filename)

        cov_dcts = [cov.as_dict() for cov in coverages]
        fields = list(cov_dcts[0].keys())

        with open(self._report_filename, "w") as outfile:
            dct_writer = csv.DictWriter(outfile, fieldnames=fields)
            dct_writer.writeheader()
            dct_writer.writerows(cov_dcts)

    def _get_all_schedule_ids(self) -> set[str]:
        """Get all unique schedule IDs."""
        more = True
        params = {"offset": 0, "limit": self._max_query_limit}
        sch_ids: list[str] = []
        while more:
            self.log.debug("List schedules: %s", params)
            resp = self._http.get(f"{self.base_url}/schedules", params=params)

            if not resp.is_success:
                self.log.error("Unexpected error: %s", resp.text)
                raise QueryError("Unexpected error")

            sch_ids.extend([schedule["id"] for schedule in resp.json()["schedules"]])

            params["offset"] += self._max_query_limit
            more = resp.json()["more"]

        self.log.info("Discovered %d schedules.", len(sch_ids))

        return set(sch_ids)

    def _get_schedule_coverages(self, schedule_ids: set[str]) -> dict[str, Coverage]:
        """Map scheduleId:ScheduleCoverage object, pulling detailed object from PD."""
        schedule_map: dict[str, Coverage] = {}

        self.log.info("Pulling %d schedules for coverage.", len(schedule_ids))

        for idx, sch_id in enumerate(schedule_ids, 1):
            self.log.debug("Pulling %s (%d of %d)", sch_id, idx, len(schedule_ids))

            coverage = self.get_schedule_coverage(sch_id)
            schedule_map.update({sch_id: coverage} if coverage else {})

        return schedule_map

    def get_schedule_coverage(self, schedule_id: str) -> Coverage | None:
        """Get ScheduleCoverage from PagerDuty with specific schedule id."""
        schobj: Coverage | None = None
        now = DateTool.utcnow_isotime()
        params = {
            "since": now,
            "until": DateTool.add_offset(now, days=self._look_ahead_days),
            "time_zone": "Etc/UTC",
        }
        resp = self._http.get(f"{self.base_url}/schedules/{schedule_id}", params=params)

        if resp.is_success:
            schobj = Coverage.build_from(resp.json())
        else:
            self.log.error("Error fetching schedule %s - %s", schedule_id, resp.text)

        return schobj


def main() -> int:
    """CLI entry."""
    args = runtime.parse_args()
    CoverageGapReport(token=args.token).run_reports()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
