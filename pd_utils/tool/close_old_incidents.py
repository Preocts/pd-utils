"""Clean up stale or ignored incidents in PagerDuty."""
from __future__ import annotations

import datetime
import logging
from typing import Any
from typing import TypedDict

import httpx

from pd_utils.model import Incident
from pd_utils.util import DateTool
from pd_utils.util import IOUtil
from pd_utils.util import PagerDutyQuery

TITLE_TAG = "[closed by automation]"
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
        self._query = PagerDutyQuery(token, email)
        self._max_query_limit = 100
        self._close_after_seconds = close_after_days * 86_400
        self._close_active = close_active
        self._close_priority = close_priority

    def run(self, inputfile: str | None = None) -> None:
        """Run the script."""
        filedate = datetime.datetime.now().strftime("%Y%m%d-%H%M")

        if inputfile:
            self.log.info("Reading input file: %s", inputfile)

            to_close_dict = IOUtil.csv_to_dict(IOUtil.read_from_file(inputfile))
            to_close = [Incident(**row) for row in to_close_dict]
            self.log.info("Read %s inactives, starting actions", len(to_close))

            successes, errors = self._close_incidents(to_close)

            IOUtil.write_to_file(
                filepath=f"close-old-incidents-{filedate}.csv",
                content=IOUtil.to_csv_string(successes),
            )
            IOUtil.write_to_file(
                filepath=f"close-old-incidents-errors-{filedate}.csv",
                content=IOUtil.to_csv_string(errors),
            )

        else:
            self.log.info("Pulling incidents from PagerDuty, this can take a while")
            all_incidents = self._get_all_incidents()
            self.log.info("Found %s open incidents", len(all_incidents))

            isolated = self._isolate_old_incidents(all_incidents)
            isolated = self._isolate_nonpriority_incidents(isolated)

            # Inactive scanning requires additional calls to PD, run last
            if not self._close_active:
                isolated = self._isolate_inactive_incidents(isolated)

            IOUtil.write_to_file(
                filepath=f"close-old-incidents-preview-{filedate}.csv",
                content=IOUtil.to_csv_string(isolated),
            )

    def _isolate_old_incidents(self, incidents: list[Incident]) -> list[Incident]:
        """Isolate old incidents from list of incidents."""
        old_incidents: list[Incident] = []
        for incident in incidents:
            delta = DateTool.to_seconds(incident.created_at, NOW.isoformat())

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
            if not incident.has_priority or self._close_priority:
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
            seconds = DateTool.to_seconds(lst_log["created_at"], NOW.isoformat())

            if seconds > self._close_after_seconds:
                self.log.debug("Incident %s has no activity", incident.incident_number)
                inactive_incidents.append(incident)
        self.log.info("Isolated %s inactive incidents", len(inactive_incidents))

        return inactive_incidents

    def _get_all_incidents(self) -> list[Incident]:
        """Pull all open incidents from PagerDuty."""
        params = {
            "time_zone": "UTC",
            "statuses[]": ["triggered", "acknowledged"],
            "date_range": "all",
        }
        self._query.set_query_target("/incidents", "incidents")
        self._query.set_query_params(params)

        incidents = [inc for inc in self._query.query_iter(self._max_query_limit)]

        self.log.info("Discovered %d incidents.", len(incidents))
        return [Incident.build_from(incident) for incident in incidents]

    def _get_newest_log_entry(self, incident_id: str) -> dict[str, Any]:
        """Pull most recent log entry from incident."""
        self._query.set_query_target(
            route=f"/incidents/{incident_id}/log_entries",
            object_name="log_entries",
        )
        self._query.set_query_params({"time_zone": "UTC"})
        resp, _, _ = self._query._query(limit=1)
        return resp[0]

    def _close_incidents(
        self,
        incidents: list[Incident],
    ) -> tuple[list[Incident], list[Incident]]:
        """Close incidents provided. Returns Success list and Error list."""
        self.log.info("Start close actions on %d incidents.", len(incidents))
        success: list[Incident] = []
        error: list[Incident] = []
        for incident in incidents:
            self.log.debug("Closing incident %s", incident.incident_number)
            if self._resolve_incident(incident.incident_id, incident.title):
                success.append(incident)
            else:
                error.append(incident)

        return success, error

    def _resolve_incident(self, incident_id: str, title: str) -> bool:
        """Mark incident resolved while updated title to include TITLE_TAG."""
        payload = {
            "incident": {
                "type": "incident_reference",
                "status": "resolved",
                "title": f"{TITLE_TAG} {title}",
            }
        }
        url = f"{self.base_url}/incidents/{incident_id}"
        resp = self._http.put(url=url, json=payload)
        if not resp.is_success:
            self.log.error("Error resolving incident: %s, '%s'", incident_id, resp.text)
        return resp.is_success
