from __future__ import annotations

from typing import Mapping

import httpx


class PagerDutyQuery:
    """Pull from API list endpoints."""

    def __init__(self, token: str, email: str) -> None:
        """Initilize httpx client for queries to list endpoints."""
        headers = {
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={token}",
            "From": email,
        }
        self._httpx = httpx.Client(headers=headers)
        self._fields: Mapping[str, str | list[str] | bool] = {}
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

    def set_query_fields(self, fields: Mapping[str, str | list[str] | bool]) -> None:
        """Set url fields for query."""
        self._fields = fields

    def set_query_target(self, route: str, object_name: str) -> None:
        """
        Set the route and object name for the query.

        Args:
            route: Examples: `/schedules` `/users` `/incident/{id}/log_entries`
            object_name: Examples: `schedules`, `users`, `log_entries`
        """
        if not route.startswith("/"):
            raise ValueError("Invalid route, must start with '/'.")

        self._route = route
        self._object_name = object_name
