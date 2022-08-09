"""
Command line handler for UserReport
"""
from __future__ import annotations

from pd_utils.report import UserReport
from pd_utils.util import DateTool
from pd_utils.util import IOUtil
from pd_utils.util import RuntimeInit


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
