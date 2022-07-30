"""Setup runtime environment for all scripts."""
from __future__ import annotations

import argparse
import logging
from typing import Sequence

from secretbox import SecretBox
from secretbox.envfile_loader import EnvFileLoader


class RuntimeInit:
    def __init__(self, prog_name: str) -> None:
        """Setup runtime environment for all scripts."""
        self.secrets = SecretBox()
        self.parser = argparse.ArgumentParser(
            prog=prog_name,
            description="Pagerduty command line utilities.",
            epilog="See: https://github.com/Preocts/pagerduty-utils",
        )

    def init_secrets(self, env_file: str | None = None) -> None:
        """
        Initialize secrets from a file and environment.

        Args:
            env_file: The path to the file containing the secrets.
        """
        self.secrets.use_loaders(EnvFileLoader(env_file))

    def init_logging(self) -> None:
        """Init logging level and format. (default: $LOGGING_LEVEL | INFO)"""
        level = self.secrets.get("LOGGING_LEVEL", "INFO")
        logging.getLogger().setLevel(level)
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        )

    def add_argument(
        self,
        flag: str,
        default: str,
        help_: str = "",
        choices: Sequence[str] | None = None,
    ) -> None:
        """
        Add a command line argument to the parser.

        Args:
            flag: The flag to use for the argument. (e.g. --flag)
            default: The default value for the argument.
            help_: The help text for the argument.
            choices: The choices for the argument.
        """
        self.parser.add_argument(
            flag,
            default=default,
            help=help_,
            choices=choices,
        )

    def parse_args(self, args: Sequence[str] | None = None) -> argparse.Namespace:
        """Parse command line arguments."""
        self.parser.add_argument(
            "--logging-level",
            help="Logging level (default: $LOGGING_LEVEL | INFO)",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default=self.secrets.get("LOGGING_LEVEL", "INFO"),
        )
        self.parser.add_argument(
            "--token",
            help="PagerDuty API Token (default: $PAGERDUTY_TOKEN)",
            default=self.secrets.get("PAGERDUTY_TOKEN", ""),
        )
        self.parser.add_argument(
            "--email",
            help="PagerDuty Email (default: $PAGERDUTY_EMAIL)",
            default=self.secrets.get("PAGERDUTY_EMAIL", ""),
        )

        parsed = (
            self.parser.parse_args() if args is None else self.parser.parse_args(args)
        )

        self.secrets.set("PAGERDUTY_TOKEN", parsed.token)
        self.secrets.set("PAGERDUTY_EMAIL", parsed.email)
        self.secrets.set("LOGGING_LEVEL", parsed.logging_level)

        return parsed
