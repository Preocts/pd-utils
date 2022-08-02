"""Clean up stale or ignored incidents in PagerDuty."""
from __future__ import annotations

import csv
import datetime
import logging
from typing import Any
from typing import TypedDict

import httpx

from pd_utils.model import Incident
from pd_utils.util import DateTool
from pd_utils.util import RuntimeInit


NOW = datetime.datetime.utcnow()


class IncidentRow(TypedDict):
    incident_url: str
    incident_id: str
    incident_number: str
    urgency: str
    severity: str
    opened_at: str
    last_status_update_at: str
    age_in_days: int


class QueryError(Exception):
    ...


class CloseOldIncidents:
    """Use to clean up and close old incidents in PagerDuty."""

    log = logging.getLogger(__name__)
    base_url = "https://api.pagerduty.com"

    def __init__(
        self,
        token: str,
        email: str,
        *,
        close_after_days: int = 10,
        close_active: bool = False,
        close_priority: bool = False,
    ) -> None:
        """
        Used to clean up and close old incidents in PagerDuty.

        Args:
            token: API v2 read/write token for PagerDuty
            email: Valid PagerDuty account email with permissions for closing incidents
            close_after_days: Incidents older than this are considered for closing
            close_after: When true, old incidents are closed regardless of activity
            close_priority: When true, consider incidents with priority for closing
        """

        headers = {
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={token}",
            "From": email,
        }

        self._http = httpx.Client(headers=headers)
        self._max_query_limit = 100
        self._close_after_seconds = close_after_days * 86_400
        self._close_active = close_active
        self._close_priority = close_priority

    def run(self, inputfile: str | None = None) -> None:
        """Run the script."""
        if inputfile:
            self.log.info("Reading input file: %s", inputfile)
            to_close = self._load_input_file(inputfile)
            self.log.info("Read %s inactives, starting actions", len(to_close))

            # self._close_incidents(to_close)

            # self._write_file("close-old-incidents", self._incidents)
            # self._write_file("close-old-incidents-errors", self._errors)

        else:
            self.log.info("Pulling incidents from PagerDuty, this can take a while")
            all_incidents = self._get_all_incidents()
            self.log.info("Found %s open incidents", len(all_incidents))

            isolated_incidents = self._isolate_old_incidents(all_incidents)
            isolated_incidents = self._isolate_nonpriority_incidents(isolated_incidents)

            # Inactive scanning requires additional calls to PD, run last
            isolated_incidents = self._isolate_inactive_incidents(isolated_incidents)

            self._write_file(isolated_incidents, "close-old-incidents-preview")

    def _load_input_file(self, inputfile: str) -> list[Incident]:
        """Load input file."""
        with open(inputfile) as f:
            reader = csv.DictReader(f)
            return [Incident(**row) for row in reader]  # type: ignore

    def _write_file(self, rows: list[Incident], filename: str) -> None:
        """Write rows to file, date and `.csv` appended to filename."""
        if not rows:
            return None

        filedate = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        filename = f"{filename}-{filedate}.csv"
        headers = list(rows[0].as_dict().keys())

        with open(filename, "w") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(row.as_dict() for row in rows)

        self.log.info("Wrote %s rows to %s", len(rows), filename)

    def _isolate_old_incidents(self, incidents: list[Incident]) -> list[Incident]:
        """Isolate old incidents from list of incidents."""
        old_incidents: list[Incident] = []
        for incident in incidents:
            delta = DateTool.to_seconds(NOW.isoformat(), incident.created_at)
            if delta > self._close_after_seconds:
                old_incidents.append(incident)
        self.log.info("Isolated %s old incidents", len(old_incidents))

        return old_incidents

    def _isolate_nonpriority_incidents(
        self,
        incidents: list[Incident],
    ) -> list[Incident]:
        """Isolate nonpriority incidents from list of incidents."""
        nonpriority_incidents: list[Incident] = []
        for incident in incidents:
            if not incident.has_priority:
                nonpriority_incidents.append(incident)
        self.log.info("Isolated %s nonpriority incidents", len(nonpriority_incidents))

        return nonpriority_incidents

    def _isolate_inactive_incidents(self, incidents: list[Incident]) -> list[Incident]:
        """Isolate inactive incidents from list of incidents."""
        inactive_incidents: list[Incident] = []

        for idx, incident in enumerate(incidents):
            if idx % 100 == 0:
                self.log.info("Checking incident %s to %s", idx, idx + 100)

            lst_log = self._get_newest_log_entry(incident.incident_id)
            seconds = DateTool.to_seconds(NOW.isoformat(), lst_log["created_at"])
            print(seconds)

            if seconds > self._close_after_seconds:
                self.log.debug("Incident %s has no activity", incident.incident_number)
                inactive_incidents.append(incident)
        self.log.info("Isolated %s inactive incidents", len(inactive_incidents))

        return inactive_incidents

    # TODO: preocts - Reused code - This needs to be extracted into a helper
    def _get_all_incidents(self) -> list[Incident]:
        """Pull all open incidents from PagerDuty."""
        more = True
        params: dict[str, Any] = {
            "time_zone": "UTC",
            "statuses[]": ["triggered", "acknowledged"],
            "offset": 0,
            "limit": self._max_query_limit,
        }
        incidents: list[dict[str, Any]] = []

        while more:
            self.log.debug("List incidents: %s", params)
            resp = self._http.get(f"{self.base_url}/incidents", params=params)

            if not resp.is_success:
                self.log.error("Unexpected error: %s", resp.text)
                raise QueryError("Unexpected error")

            incidents.extend(resp.json()["incidents"])

            params["offset"] += self._max_query_limit
            more = resp.json()["more"]

        self.log.info("Discovered %d incidents.", len(incidents))

        return [Incident.build_from(incident) for incident in incidents]

    # TODO: preocts - Reused code - This needs to be extracted into a helper
    def _get_newest_log_entry(self, incident_id: str) -> dict[str, Any]:
        """Pull most recent log entry from incident."""

        params: dict[str, Any] = {
            "time_zone": "UTC",
            "offset": 0,
            "limit": 1,
        }

        self.log.debug("List log entry: %s", params)
        resp = self._http.get(
            url=f"{self.base_url}/incidents/{incident_id}/log_entries",
            params=params,
        )

        if not resp.is_success:
            self.log.error("Unexpected error: %s", resp.text)
            raise QueryError("Unexpected error")

        return resp.json()["log_entries"][0]


def main(args_in: list[str] | None = None) -> int:
    """Run the script."""
    runtime = RuntimeInit("close-old-incidents")
    runtime.init_secrets()
    runtime.add_standard_arguments()
    runtime.add_argument(
        "--inputfile",
        "",
        "Provide a csv file to work from. If not provided a new file will be created.",
    )
    runtime.add_argument(
        flag="--close-after-days",
        default="10",
        help_="Incidents older than this are considered for closing",
    )
    runtime.parser.add_argument(
        "--close-active",
        action="store_true",
        help="When present, old incidents are closed regardless of activity",
    )
    runtime.parser.add_argument(
        "--close-priority",
        action="store_true",
        help="When present, consider incidents with priority for closing",
    )
    runtime.init_logging()
    args = runtime.parse_args(args_in)

    client = CloseOldIncidents(
        token=runtime.secrets.get("PAGERDUTY_TOKEN"),
        email=runtime.secrets.get("PAGERDUTY_EMAIL"),
        close_after_days=int(args.close_after_days),
        close_active=args.close_active,
        close_priority=args.close_priority,
    )
    client.run(args.inputfile)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
