"""
Pull a user report including general information on user accounts.
"""
from __future__ import annotations

import logging

from pd_utils.model import User
from pd_utils.util import DateTool
from pd_utils.util import IOUtil
from pd_utils.util import PagerDutyQuery
from pd_utils.util import RuntimeInit


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

    def run_report(
        self,
        team_ids: list[str] | None = None,
        base_roles: list[str] | None = None,
        team_roles: list[str] | None = None,
    ) -> str:
        """
        Run report. Returns csv string.

        Valid base roles include `admin`, `limited_user`, `observer`, `owner`,
        `read_only_user`, `restricted_access`, `read_only_limited_user`, or `user`

        Valid team roles include `observer`, `responder`, `manager`

        Args:
            team_ids: List of team ids to isolate in report
            base_roles: List of base roles to isolate in report
            team_roles: List of team roles to isolate in report
        """
        self._query.set_query_target("/users", "users")
        self._query.set_query_params(
            {
                "include[]": ["notification_rules", "teams", "contact_methods"],
                "team_ids[]": team_ids or None,
            }
        )
        users: list[User] = []
        for resps in self._query.run_iter(limit=self._max_query_limit):
            self.log.debug("Pulling %d users...", self._max_query_limit)
            users.extend([User.build_from(resp) for resp in resps])
        self.log.info("Discovered %d users in total.", len(users))

        users = self._isolate_by_base_role(users, base_roles or [])
        self.log.info("Isolated %d users by base role.", len(users))

        users = self._isolate_by_team_role(users, team_roles or [])
        self.log.info("Isolated %d users by team role.", len(users))

        return IOUtil.to_csv_string(users)

    @staticmethod
    def _isolate_by_base_role(users: list[User], roles: list[str]) -> list[User]:
        """Return User objects that have given base roles or all if roles is empty."""
        if not roles:
            return users
        return [user for user in users if user.base_role in roles]

    @staticmethod
    def _isolate_by_team_role(users: list[User], roles: list[str]) -> list[User]:
        """Return User objects that have given team role or all if roles is empty."""
        if not roles:
            return users
        iso: list[User] = []
        for user in users:
            if any([getattr(user, f"{role}_in") for role in roles]):
                iso.append(user)
        return iso


def main(_args: list[str] | None = None) -> int:
    """Main point of entry for CLI."""
    runtime = RuntimeInit("user-report")
    runtime.init_secrets()
    runtime.add_standard_arguments(email=False)
    runtime.add_argument(
        flag="--team_ids",
        default="",
        help_="Comma separated list of team ids to include in report.",
        nargs="*",
    )
    runtime.add_argument(
        flag="--base_roles",
        default="",
        help_="Comma separated list of base roles applied as a filter to report. ",
        choices=[
            "admin",
            "limited_user",
            "observer",
            "owner",
            "read_only_user",
            "restricted_access",
            "read_only_limited_user",
            "user",
        ],
        nargs="*",
    )
    runtime.add_argument(
        flag="--team_roles",
        default="",
        help_="Comma separated list of team roles applied as a filter to report.",
        choices=["manager", "observer", "responder"],
        nargs="*",
    )
    args = runtime.parse_args(_args)
    runtime.init_logging()

    print("Starting User Report, this pull can take some time.")
    report = UserReport(args.token).run_report(
        team_ids=args.team_ids,
        base_roles=args.base_roles,
        team_roles=args.team_roles,
    )

    now = DateTool.utcnow_isotime().split("T")[0]
    IOUtil.write_to_file(f"user_report{now}.csv", report)
    print(f"Report saved to user_report{now}.csv")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
