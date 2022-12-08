from __future__ import annotations

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from pd_utils.util import RuntimeInit
from pd_utils.util.pagerduty_api import PagerDutyAPI

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

    assert "token" in args and args.token == ""
    assert "email" in args and args.email == ""
    assert "logging_level" in args and args.logging_level == "ERROR"
    assert "timeout" in args and args.timeout == 60


def test_add_standard_arguments_toggled_off(runtime: RuntimeInit) -> None:
    runtime.add_standard_arguments(
        token=False,
        email=False,
        loglevel=False,
        timeout=False,
    )

    args = runtime.parse_args([])

    assert "token" not in args
    assert "email" not in args
    assert "logging_level" not in args
    assert "timeout" not in args


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


def test_get_pagerduty_connection(runtime: RuntimeInit) -> None:
    runtime.init_secrets(ENV_FILE)
    expected_auth = f'Token token={runtime.secrets.get("PAGERDUTY_TOKEN")}'
    expected_email = runtime.secrets.get("PAGERDUTY_EMAIL")
    result = runtime.get_pagerduty_connection()

    assert isinstance(result, PagerDutyAPI)
    assert result._http.headers["authorization"] == expected_auth
    assert result._http.headers["from"] == expected_email


def test_get_pagerduty_connection_override_args(runtime: RuntimeInit) -> None:
    runtime.init_secrets(ENV_FILE)
    expected_auth = "Token token=override_mock"
    expected_email = "override_email"
    result = runtime.get_pagerduty_connection("override_mock", "override_email", 1)

    assert isinstance(result, PagerDutyAPI)
    assert result._http.headers["authorization"] == expected_auth
    assert result._http.headers["from"] == expected_email
