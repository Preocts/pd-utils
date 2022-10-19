from __future__ import annotations

from unittest.mock import patch

from pd_utils.cli import coverage_gap_report_cli


def test_main() -> None:
    with patch.object(
        coverage_gap_report_cli.CoverageGapReport, "run_reports"
    ) as mocked:
        mocked.return_value = ("", "")
        coverage_gap_report_cli.main(_args=[])

        mocked.assert_called_once()
