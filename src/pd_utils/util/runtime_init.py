"""Setup runtime environment for all scripts."""
from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from runtime_yolk import Yolk


class RuntimeInit:
    def __init__(self, prog_name: str, *, _config_name: str = "pd-util") -> None:
        """Setup runtime environment for all scripts."""
        self.yolk = Yolk()
        self.yolk.load_env()
        self.yolk.load_config(_config_name)
        self.yolk.set_logging()

        self.parser = argparse.ArgumentParser(
            prog=prog_name,
            description="Pagerduty command line utilities.",
            epilog="See: https://github.com/Preocts/pagerduty-utils",
        )

    def get_logger(self) -> logging.Logger:
        """Get the root logger."""
        return self.yolk.get_logger()

    def add_argument(
        self,
        flag: str,
        default: str,
        help_: str = "",
        choices: Sequence[str] | None = None,
        nargs: str | int | None = None,
    ) -> None:
        """
        Add a command line argument to the parser.

        Args:
            flag: The flag to use for the argument. (e.g. --flag)
            default: The default value for the argument.
            help_: The help text for the argument.
            choices: The choices for the argument.
            nargs: Number of argugments expected for flag
        """
        self.parser.add_argument(
            flag,
            default=default,
            help=help_,
            choices=choices,
            nargs=nargs,  # type: ignore # (preocts) None is valid here
        )

    def add_standard_arguments(
        self,
        *,
        token: bool = True,
        email: bool = True,
        loglevel: bool = True,
    ) -> None:
        """
        Add most common command line arguments to the parser.

        Keyword Args:
            token: When true collects optional API token
            email: When true collects optional PagerDuty account email
            loglevel: When true collects optional logging level
        """
        if token:
            self.parser.add_argument(
                "--token",
                help="PagerDuty API Token (default: $PAGERDUTY_TOKEN)",
                default=self.yolk.config.get("DEFAULT", "token", fallback=""),
            )
        if email:
            self.parser.add_argument(
                "--email",
                help="PagerDuty Email (default: $PAGERDUTY_EMAIL)",
                default=self.yolk.config.get("DEFAULT", "email", fallback=""),
            )
        if loglevel:
            self.parser.add_argument(
                "--logging-level",
                help="Logging level (default: $LOGGING_LEVEL | ERROR)",
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                default=self.yolk.config.get(
                    "DEFAULT",
                    "logging_level",
                    fallback="ERROR",
                ),
            )

    def parse_args(self, args: Sequence[str] | None = None) -> argparse.Namespace:
        """Parse command line arguments."""
        parsed = (
            self.parser.parse_args() if args is None else self.parser.parse_args(args)
        )
        # Inject overrides to secrets if in parser
        if "token" in parsed:
            self.yolk.config.set("DEFAULT", "token", parsed.token)
        if "email" in parsed:
            self.yolk.config.set("DEFAULT", "email", parsed.email)
        if "logging_level" in parsed:
            self.yolk.config.set("DEFAULT", "logging_level", parsed.logging_level)

        return parsed
