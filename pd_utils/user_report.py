"""
Pull a user report including general information on user accounts.
"""
from __future__ import annotations

import logging
from typing import Any
from typing import NamedTuple

from pd_utils.model import UserReportRow
from pd_utils.model import UserTeam
from pd_utils.util import DateTool
from pd_utils.util import IOUtil
from pd_utils.util import PagerDutyQuery
from pd_utils.util import RuntimeInit


class _Team(NamedTuple):
    team_name: str
    team_id: str


class UserReport:
    """Pull a user report including general information on user accounts."""

    log = logging.getLogger()

    def __init__(self, token: str, *, max_query_limit: int = 100) -> None:
        """
        Required: PagerDuty API v2 token with read access.

        Args:
            max_query_limit: Number of objects to request at once from PD (max: 100)
        """
        self._query = PagerDutyQuery(token)
        self._max_query_limit = max_query_limit

    def run_report(self, team_ids: list[str] | None = None) -> str:
        """
        Run report. Returns csv string.

        Args:
            team_ids: List of team ids to isolate in report
        """
        self._query.set_query_target("/users", "users")
        self._query.set_query_params(
            {
                "include[]": ["notification_rules", "contact_methods"],
                "team_ids[]": team_ids or None,
            }
        )
        self.log.info("Pulling user object, this can take a momement.")

        user_map, teams = self._get_users_and_teams()

        self.log.info("Discovered %d users and %d teams.", len(user_map), len(teams))

        user_teams = self._get_team_memberships(teams)

        self._hydrate_team_membership(user_map, user_teams)

        return IOUtil.to_csv_string(list(user_map.values()))

    def _get_users_and_teams(self) -> tuple[dict[str, UserReportRow], set[_Team]]:
        """Pull all users and unique team names discovered."""
        user_map: dict[str, UserReportRow] = {}
        teams: set[_Team] = set()
        for resps in self._query.run_iter(limit=self._max_query_limit):
            for resp in resps:
                user = UserReportRow.build_from(resp)
                user_map[user.id] = user
                teams = teams.union(self._extract_teams(resp["teams"]))
        return user_map, teams

    def _extract_teams(self, teams: list[dict[str, Any]] | None) -> set[_Team]:
        """Extract unique team_ids from list of teams"""
        return {_Team(team["summary"], team["id"]) for team in teams or []}

    def _get_team_memberships(self, teams: set[_Team]) -> list[UserTeam]:
        """Get membership details of teams from PagerDuty."""
        # TODO: REFACTOR

        self.log.info("Pulling membership details of %d teams.", len(teams))
        self._query.set_query_params({})
        user_teams: list[UserTeam] = []
        for team_name, team_id in teams:
            self._query.set_query_target(f"/teams/{team_id}/members", "members")
            for resp in self._query.run_iter(limit=self._max_query_limit):
                for member in resp:
                    user_teams.append(
                        UserTeam(
                            user_id=member["user"]["id"],
                            team_id=team_id,
                            team_name=team_name,
                            team_role=member["role"],
                        )
                    )
        self.log.info("Discovered %d membership details.", len(user_teams))
        return user_teams

    def _hydrate_team_membership(
        self,
        user_map: dict[str, UserReportRow],
        user_teams: list[UserTeam],
    ) -> None:
        """Hydrate team membership by role into user_map."""
        for user_team in user_teams:
            team = f"{user_team.team_name}, {user_team.team_id}"
            attr = f"{user_team.team_role}_in"
            if getattr(user_map[user_team.user_id], attr) is None:
                setattr(user_map[user_team.user_id], attr, [])
            getattr(user_map[user_team.user_id], attr).append(team)


def main(_args: list[str] | None = None) -> int:
    """Main point of entry for CLI."""
    runtime = RuntimeInit("user-report")
    runtime.init_secrets()
    runtime.add_standard_arguments(email=False)
    runtime.add_argument(
        flag="--team_ids",
        default="",
        help_="List of team ids to include in report.",
        nargs="*",
    )
    args = runtime.parse_args(_args)
    runtime.init_logging()

    print("Starting User Report, this pull can take some time.")
    report = UserReport(args.token).run_report(team_ids=args.team_ids)

    now = DateTool.utcnow_isotime().split("T")[0]
    IOUtil.write_to_file(f"user_report{now}.csv", report)
    print(f"Report saved to user_report{now}.csv")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
