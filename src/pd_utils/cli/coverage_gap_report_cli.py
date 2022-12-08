"""
Command line handler for CoverageGapReport
"""
from __future__ import annotations

from pd_utils.report import CoverageGapReport
from pd_utils.util import datetool
from pd_utils.util import ioutil
from pd_utils.util import RuntimeInit


def main(*, _args: list[str] | None = None) -> int:
    """CLI entry."""
    runtime = RuntimeInit("coverage-gap-report")
    runtime.add_standard_arguments(email=False)
    runtime.add_argument(
        flag="--look-ahead",
        default="14",
        help_="Number of days to look ahead for gaps, default 14",
    )
    args = runtime.parse_args(_args)
    client = CoverageGapReport(token=args.token, look_ahead_days=int(args.look_ahead))
    schedule_report, escalation_report = client.run_reports()

    now = datetool.utcnow_isotime().split("T")[0]
    ioutil.write_to_file(f"schedule_gap_report{now}.csv", schedule_report)
    ioutil.write_to_file(f"escalation_rule_gap_report{now}.csv", escalation_report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
