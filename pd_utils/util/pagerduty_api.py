from __future__ import annotations

import json
import logging
from collections.abc import Generator
from typing import Any

import httpx


class PagerDutyAPI:
    """Pull from API list endpoints."""

    log = logging.getLogger(__name__)
    base_url = "https://api.pagerduty.com"

    class QueryError(Exception):
        ...

    def __init__(self, token: str, email: str | None = None) -> None:
        """Initilize httpx client for queries to list endpoints."""
        headers = {
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={token}",
        }
        headers.update({"From": email} if email else {})

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
        self._params = {k: v for k, v in params.items() if v is not None}

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

    def _query(
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

    def query_iter(self, limit: int = 100) -> Generator[dict[str, Any], None, None]:
        """Iterate through responses from PagerDuty API."""
        more = True
        offset = 0

        while more:
            results, more, _ = self._query(offset=offset, limit=limit)
            offset += limit
            yield from results

    def get(
        self,
        route: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Get result from given route endpoint."""
        params = {k: v for k, v in params.items() if v is not None} if params else None
        resp = self._http.get(f"{self.base_url}{route}", params=params)

        if not resp.is_success:
            self.log.error("Get failed: %d, %s", resp.status_code, resp.text)

        return resp.json() if resp.is_success else None

    def put(
        self,
        route: str,
        payload: dict[str, Any] | None = None,
    ) -> str | dict[str, Any] | None:
        """Put payload to given route endpoint."""
        resp = self._http.put(f"{self.base_url}{route}", json=payload)

        if not resp.is_success:
            self.log.error("Put failed: %d, %s", resp.status_code, resp.text)
        try:
            return resp.json() if resp.is_success else None
        except json.JSONDecodeError:
            return resp.text if resp.text else None
