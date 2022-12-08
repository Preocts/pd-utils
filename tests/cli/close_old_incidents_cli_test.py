from __future__ import annotations

from unittest.mock import patch

from pd_utils.cli import close_old_incidents_cli


def test_main_no_optional_args() -> None:

    with patch.object(close_old_incidents_cli, "CloseOldIncidents") as mockclass:
        close_old_incidents_cli.main(["--token", "mock", "--email", "mock@mock.com"])
        kwargs = mockclass.call_args.kwargs

    assert kwargs["close_after_days"] == 10
    assert kwargs["close_active"] is False
    assert kwargs["close_priority"] is False


def test_main_optional_args() -> None:

    with patch.object(close_old_incidents_cli, "CloseOldIncidents") as mockclass:
        close_old_incidents_cli.main(
            [
                "--token",
                "mock",
                "--email",
                "mock@mock.com",
                "--close-active",
                "--close-priority",
                "--close-after-days=5",
            ]
        )
        kwargs = mockclass.call_args.kwargs

    assert kwargs["close_after_days"] == 5
    assert kwargs["close_active"] is True
    assert kwargs["close_priority"] is True
