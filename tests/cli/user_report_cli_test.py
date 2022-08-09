from __future__ import annotations

from unittest.mock import patch

from pd_utils.cli import user_report_cli


def test_main() -> None:

    with patch.object(
        user_report_cli.UserReport, "run_report", return_value=""
    ) as mock:

        result = user_report_cli.main([])

        assert mock.call_count == 1
        assert result == 0
