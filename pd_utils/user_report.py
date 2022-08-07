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

    def run_report(self, team_ids: list[str] | None = None) -> str:
        """
        Run report. Returns csv string.

        Args:
            team_ids: List of team ids to isolate in report
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

        return IOUtil.to_csv_string(users)


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
