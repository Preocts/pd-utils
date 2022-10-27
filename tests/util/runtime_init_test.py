from __future__ import annotations

import logging
import os
from collections.abc import Generator
from configparser import NoOptionError
from unittest.mock import patch

import pytest
from _pytest.logging import LogCaptureFixture
from pd_utils.util import RuntimeInit

ENV_FILE = "tests/fixture/mockenv"
INI_FILE = "tests/fixture/mock-pd-util"


@pytest.fixture(autouse=True)
def patch_environ() -> Generator[None, None, None]:
    with patch.dict(os.environ, {}):
        yield None


@pytest.fixture
def runtime() -> Generator[RuntimeInit, None, None]:
    rt = RuntimeInit("testing", _config_name="testingonly")
    rt.yolk.load_env(ENV_FILE)
    rt.yolk.load_config(INI_FILE)
    rt.yolk.set_logging()
    yield rt


@pytest.mark.usefixtures("runtime")
def test_init_secrets() -> None:

    assert os.getenv("PAGERDUTY_TOKEN") == "token"
    assert os.getenv("PAGERDUTY_EMAIL") == "email"
    assert os.getenv("LOGGING_LEVEL") == "CRITICAL"


def test_init_config(runtime: RuntimeInit) -> None:

    assert runtime.yolk.config.get("DEFAULT", "logging_level") == "CRITICAL"
    assert runtime.yolk.config.get("DEFAULT", "token") == "token"
    assert runtime.yolk.config.get("DEFAULT", "email") == "email"


def test_init_with_no_config() -> None:
    # Run without loading mock files, assert things are as we assume
    runtime = RuntimeInit("testing", _config_name="testingonly")
    assert runtime.yolk.config.get("DEFAULT", "logging_level") == "ERROR"
    with pytest.raises(NoOptionError):
        assert runtime.yolk.config.get("DEFAULT", "token") == ""
    with pytest.raises(NoOptionError):
        assert runtime.yolk.config.get("DEFAULT", "email") == ""


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
    logger = logging.getLogger()
    prior_level = logger.level
    try:

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

    assert args.token == "token"
    assert args.email == "email"
    assert args.logging_level == "CRITICAL"


def test_environ_parse_arg_defaults(runtime: RuntimeInit) -> None:
    runtime.yolk.config.set("DEFAULT", "token", "TOKEN")
    runtime.yolk.config.set("DEFAULT", "email", "EMAIL")
    runtime.yolk.config.set("DEFAULT", "logging_level", "LOGGING_LEVEL")
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
