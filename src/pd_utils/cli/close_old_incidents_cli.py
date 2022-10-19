"""Command line handler for CloseOldIncidents."""
from __future__ import annotations

from pd_utils.tool import CloseOldIncidents
from pd_utils.util import RuntimeInit


def main(args_in: list[str] | None = None) -> int:
    """Run the script."""
    runtime = RuntimeInit("close-old-incidents")
    runtime.init_secrets()
    runtime.add_standard_arguments()
    runtime.add_argument(
        "--inputfile",
        "",
        "Provide a csv file to work from. If not provided a new file will be created.",
    )
    runtime.add_argument(
        flag="--close-after-days",
        default="10",
        help_="Incidents older than this are considered for closing (default: 10)",
    )
    runtime.parser.add_argument(
        "--close-active",
        action="store_true",
        help="When present, old incidents are closed regardless of activity",
    )
    runtime.parser.add_argument(
        "--close-priority",
        action="store_true",
        help="When present, consider incidents with priority for closing",
    )
    runtime.init_logging()
    args = runtime.parse_args(args_in)

    client = CloseOldIncidents(
        token=runtime.secrets.get("PAGERDUTY_TOKEN"),
        email=runtime.secrets.get("PAGERDUTY_EMAIL"),
        close_after_days=int(args.close_after_days),
        close_active=args.close_active,
        close_priority=args.close_priority,
    )
    client.run(args.inputfile)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
