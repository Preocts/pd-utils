"""
Send an Alert Event to PagerDuty.

https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview#getting-started
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from http.client import HTTPSConnection
from typing import Any

__all__ = ["build_alert", "send_alert"]

log = logging.getLogger(__name__)


def build_alert(
    routing_key: str,
    title: str,
    alert_body: str,
    dedup: str,
) -> dict[str, Any]:
    """
    Build the payload for an event alert.

    Args
        routing_key: Routing key or Inegration key (apiv2) of target in PagerDuty
        title: Title of alert
        alert_body: UTF-8 string of custom message for alert. Shown in incident body
        dedup: Any string, max 255, characters used to deduplicate alerts

    Returns
        Dictionary of alert body for JSON serialization
    """
    return {
        "routing_key": routing_key,
        "event_action": "trigger",
        "dedup_key": dedup,
        "payload": {
            "summary": title,
            "source": "custom_event",
            "severity": "critical",
            "custom_details": {
                "alert_body": alert_body,
            },
        },
    }


def send_alert(
    routing_key: str,
    title: str,
    alert_body: str,
    dedup: str | None = None,
) -> None:
    """
    Send PagerDuty Alert.

    Args
        routing_key: Routing key or Inegration key (apiv2) of target in PagerDuty
        title: Title of the alert.
        alert_body: UTF-8 string of custom message for alert. Shown in incident body
        dedup: Any string, max 255, characters used to deduplicate alerts

    Returns
        None
    """
    # If no dedup is given, use epoch timestamp
    if dedup is None:
        dedup = str(datetime.utcnow().timestamp())
    url = "events.pagerduty.com"
    route = "/v2/enqueue"

    conn = HTTPSConnection(host=url, port=443)
    alert = build_alert(routing_key, title, alert_body, dedup)
    conn.request("POST", route, json.dumps(alert))
    result = conn.getresponse()

    log.info("Alert status: %s", result.status)
    log.info("Alert response: %s", result.read())


def console_handler() -> int:
    """For CLI use."""
    logging.basicConfig(level="INFO")
    if 4 > len(sys.argv) or len(sys.argv) > 5:
        print(
            'Use: python -m pd_alert "Routing Key" '
            '"Alert Title" "Alert Body" ["dedup_key"]'
        )
        return 1
    send_alert(*sys.argv[1:])

    return 0


if __name__ == "__main__":
    raise SystemExit(console_handler())
