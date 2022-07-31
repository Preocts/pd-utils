from __future__ import annotations

import logging

import pytest
from _pytest.logging import LogCaptureFixture

from pd_utils.util import RuntimeInit

ENV_FILE = "tests/fixture/mockenv"


@pytest.fixture
def runtime() -> RuntimeInit:
    return RuntimeInit("testing")


def test_init_secrets(runtime: RuntimeInit) -> None:
    runtime.init_secrets(ENV_FILE)

    assert runtime.secrets.get("PAGERDUTY_TOKEN") == "token"
    assert runtime.secrets.get("PAGERDUTY_EMAIL") == "email"
    assert runtime.secrets.get("LOGGING_LEVEL") == "CRITICAL"


def test_add_standard_arguments(runtime: RuntimeInit) -> None:
    runtime.add_standard_arguments()

    args = runtime.parse_args([])

    assert "token" in args
    assert "email" in args
    assert "logging_level" in args


def test_add_standard_arguments_toggled_off(runtime: RuntimeInit) -> None:
    runtime.add_standard_arguments(token=False, email=False, loglevel=False)

    args = runtime.parse_args([])

    assert "token" not in args
    assert "email" not in args
    assert "logging_level" not in args


def test_init_logging(runtime: RuntimeInit, caplog: LogCaptureFixture) -> None:
    prior_level = logging.getLogger().level
    logger = logging.getLogger("init_logging")
    try:
        runtime.secrets.set("LOGGING_LEVEL", "CRITICAL")
        runtime.init_logging()

        logger.error("error")
        logger.critical("critical")

    finally:
        # Restore logging level at root to avoid pollution
        logging.getLogger().setLevel(prior_level)

    assert "error" not in caplog.text
    assert "critical" in caplog.text


def test_empty_parse_arg_results(runtime: RuntimeInit) -> None:
    runtime.add_standard_arguments()

    args = runtime.parse_args([])

    assert args.token == ""
    assert args.email == ""
    assert args.logging_level == "INFO"


def test_environ_parse_arg_defaults(runtime: RuntimeInit) -> None:
    runtime.secrets.set("PAGERDUTY_TOKEN", "TOKEN")
    runtime.secrets.set("PAGERDUTY_EMAIL", "EMAIL")
    runtime.secrets.set("LOGGING_LEVEL", "LOGGING_LEVEL")
    runtime.add_standard_arguments()

    args = runtime.parse_args([])

    assert args.token == "TOKEN"
    assert args.email == "EMAIL"
    assert args.logging_level == "LOGGING_LEVEL"


def test_parse_arg_cli(runtime: RuntimeInit) -> None:
    runtime.add_standard_arguments()
    cli = ["--token", "MOCKTOKEN", "--email", "MOCKEMAIL"]

    args = runtime.parse_args(cli)

    assert args.token == "MOCKTOKEN"
    assert args.email == "MOCKEMAIL"


def test_add_arg(runtime: RuntimeInit) -> None:
    runtime.add_argument("--TEST", "empty", "Goodbye")

    args = runtime.parse_args(["--TEST", "Hello"])

    assert args.TEST == "Hello"
