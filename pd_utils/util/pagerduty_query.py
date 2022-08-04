from __future__ import annotations

import logging
from typing import Any
from typing import Generator

import httpx


class PagerDutyQuery:
    """Pull from API list endpoints."""

    log = logging.getLogger(__name__)
    base_url = "https://api.pagerduty.com"

    class QueryError(Exception):
        ...

    def __init__(self, token: str, email: str) -> None:
        """Initilize httpx client for queries to list endpoints."""
        headers = {
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={token}",
            "From": email,
        }
        self._http = httpx.Client(headers=headers)
        self._params: dict[str, Any] = {}
        self._route: str | None = None
        self._object_name: str | None = None

    @property
    def object_name(self) -> str:
        """Object being returned by query."""
        if not self._object_name:
            raise ValueError("Object name not set.")
        return self._object_name

    @property
    def route(self) -> str:
        """Route being queried."""
        if not self._route:
            raise ValueError("Route not set.")
        return self._route

    def set_query_params(self, params: dict[str, Any]) -> None:
        """Set url fields for query."""
        self._params = params

    def set_query_target(self, route: str, object_name: str) -> None:
        """
        Set the route and object name for the query.

        Args:
            route: Examples: `/schedules` `/users` `/incidents/{id}/log_entries`
            object_name: Examples: `schedules`, `users`, `log_entries`
        """
        if not route.startswith("/"):
            raise ValueError("Invalid route, must start with '/'.")

        self._route = route
        self._object_name = object_name

    def run(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        total: bool = False,
    ) -> tuple[list[dict[str, Any]], bool, int]:
        """
        Run query.

        Keyword Args:
            offset: Starting point of query, used for pagination
            limit: Max results to return per query (Max: 100)
            total: When true, total objects are returned

        Returns:
            ([response], more, total)
            response: List of objects returned by query, can be empty
            more: True if more results remain after offset + limit
            total: # of objects total or 0
        """
        params = {
            "offset": offset,
            "limit": limit,
            "total": total,
            **self._params,
        }

        self.log.debug("List %s: %s", self._object_name, params)
        resp = self._http.get(f"{self.base_url}{self.route}", params=params)

        if not resp.is_success:
            self.log.error("Unexpected error: %s", resp.text)
            raise self.QueryError("Unexpected error")

        more_: bool = resp.json().get("more") or False
        total_: int = resp.json().get("total") or 0

        self.log.debug("Pulled %d objects.", len(resp.json()[self.object_name]))

        return resp.json()[self.object_name], more_, total_

    def run_iter(self, limit: int = 100) -> Generator[list[dict[str, Any]], None, None]:
        """Iterate through responses from PagerDuty API."""
        more = True
        offset = 0

        while more:
            results, more, _ = self.run(offset=offset, limit=limit)
            offset += limit
            yield results
