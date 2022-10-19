from __future__ import annotations

import json
import sys
from collections.abc import Generator
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pd_utils.tool import simple_alert


@pytest.fixture
def mock_http() -> Generator[MagicMock, None, None]:
    read = MagicMock(return_value="All good")
    resp = MagicMock(status=202, read=read)
    getresp = MagicMock(return_value=resp)
    conn = MagicMock(getresponse=getresp, request=MagicMock())
    with patch.object(simple_alert, "HTTPSConnection", conn):
        yield conn


def test_build_alert() -> None:
    alert = simple_alert.build_alert("routing", "title", "body", "dedup")

    assert alert["routing_key"] == "routing"
    assert alert["dedup_key"] == "dedup"
    assert alert["payload"]["summary"] == "title"
    assert alert["payload"]["custom_details"]["alert_body"] == "body"


def test_send_alert_auto_dedup(mock_http: MagicMock) -> None:
    simple_alert.send_alert("routing", "title", "body")
    alert = json.loads(mock_http().request.call_args.args[2])

    assert float(alert["dedup_key"])


def test_send_alert_set_dedup(mock_http: MagicMock) -> None:
    simple_alert.send_alert("routing", "title", "body", "egg")
    alert = json.loads(mock_http().request.call_args.args[2])

    assert alert["dedup_key"] == "egg"


def test_console_handler_0_exit_4_args(mock_http: MagicMock) -> None:
    with patch.object(sys, "argv", ["simple_alert.py", "route", "title", "body"]):
        result = simple_alert.console_handler()

    assert result == 0


def test_console_handler_0_exit_5_args(mock_http: MagicMock) -> None:
    with patch.object(sys, "argv", ["simple_alert.py", "route", "title", "body", "0"]):
        result = simple_alert.console_handler()

    assert result == 0


def test_console_handler_1_exit_3_args(mock_http: MagicMock) -> None:
    with patch.object(sys, "argv", ["simple_alert.py", "route", "title"]):
        result = simple_alert.console_handler()

    assert result == 1


def test_console_handler_1_exit_6_args(mock_http: MagicMock) -> None:
    with patch.object(sys, "argv", ["simple_alert", "route", "title", "1", "1", "1"]):
        result = simple_alert.console_handler()

    assert result == 1
