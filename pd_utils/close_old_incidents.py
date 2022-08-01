"""Clean up stale or ignored incidents in PagerDuty."""
from __future__ import annotations

import datetime
import logging
from typing import Any
from typing import Dict
from typing import TypedDict

import httpx

from pd_utils.util import RuntimeInit

# import csv
# from pd_utils.util import DateTool


EXPIRE_DAYS = 10  # Number of days a incident can be open before it is closed
FILEDATE = datetime.datetime.now().strftime("%Y-%m-%dT%H.%M.%SZ")
NOW = datetime.datetime.now()

Incident = Dict[str, Any]

runtime = RuntimeInit("close-old-incidents")
runtime.init_secrets()
runtime.init_logging()


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
        self._max_query_limit = 1
        self._incidents: list[IncidentRow] = []
        self._errors: list[IncidentRow] = []

    # TODO: preocts - Reused code - This needs to be extracted into a helper
    def _get_all_incidents(self) -> list[dict[str, Any]]:
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

        return incidents

    # TODO: preocts - Reused code - This needs to be extracted into a helper
    def _get_newest_log_entry(self, incident_id: str) -> list[dict[str, Any]]:
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

        return resp.json()["log_entries"]


if __name__ == "__main__":
    client = CloseOldIncidents(
        token=runtime.secrets.get("PAGERDUTY_TOKEN"),
        email=runtime.secrets.get("PAGERDUTY_EMAIL"),
    )
    resp = client._get_all_incidents()
    for incident in resp:
        client._get_newest_log_entry(incident["id"])

    raise SystemExit()
