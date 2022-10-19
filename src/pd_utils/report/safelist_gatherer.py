"""
Gather PagerDuty webhook IP safelist from their help documents repo.

IPs pulled can include both US and EU ranges or from a specific region.

Support Documentation:

https://support.pagerduty.com/docs/safelist-ips#webhooks

Developer Documentation:

https://developer.pagerduty.com/docs/ZG9jOjQ4OTcxMDMx-webhook-i-ps

Documentation Repo:

https://github.com/PagerDuty/developer-docs

Target sources:

https://developer.pagerduty.com/ip-safelists/webhooks-us-service-region-json

https://developer.pagerduty.com/ip-safelists/webhooks-eu-service-region-json

Example Usage:

    Output to console:
    Optional "us" or "eu" will limit results to that region. Default is both regions

        $ pd-ip-gatherer [eu|us]

    Importing as module:

        import pd_ip_gatherer

        full_ip_list = pd_ip_gatherer.get_all_safelist()
        eu_ip_list = pd_ip_gatherer.get_eu_safelist()
        us_ip_list = pd_ip_gatherer.get_us_safelist()
"""
from __future__ import annotations

import json
import logging
import sys
from http.client import HTTPSConnection


SOURCE_ROUTES: dict[str, list[str]] = {
    "us": [
        "developer.pagerduty.com",
        "/ip-safelists/webhooks-us-service-region-json",
    ],
    "eu": [
        "developer.pagerduty.com",
        "/ip-safelists/webhooks-eu-service-region-json",
    ],
}

TIMEOUT_SECONDS = 3

log = logging.getLogger(__name__)


def _get_url_page(url: str, route: str) -> str:
    """
    HTTPS GET request a url, return the text of the response.

    Args:
        url: URL of page to pull, exclude HTTPS:// (e.g. "app.pagerduty.com")
        route: Route following url. e.g. "/webhook_ip"

    Returns:
        String content returned from GET of target url/route, can be empty
    """
    conn = HTTPSConnection(host=url, timeout=TIMEOUT_SECONDS)

    conn.request("GET", route if route.startswith("/") else f"/{route}")
    resp = conn.getresponse()

    if resp.status not in range(200, 300):
        log.error("Invalid response from %s, %s. %d", url, route, resp.status)
        return ""

    return resp.read().decode()


def _get_webhooks_ips(region: str | None = None, new_source: bool = True) -> list[str]:
    """
    Pull webhook IPs from PagerDuty's source(s).

    Args:
        region: Valid values are `US` or `EU`, case agnostic. `None` will pull both
        new_source: Use the new developer doc source for IPs.
    """
    regions = [region.lower()] if region is not None else list(SOURCE_ROUTES.keys())

    full_list: list[str] = []

    for target_region in regions:

        url, route = SOURCE_ROUTES[target_region]

        result = _get_url_page(url, route)

        full_list.extend(json.loads(result) if result else [])

    return full_list


def get_all_safelist() -> set[str]:
    """Return all safelist IPs (US and Euro region) in the form of a set."""
    us_set = get_us_safelist()
    eu_set = get_eu_safelist()
    return us_set.union(eu_set)


def get_us_safelist() -> set[str]:
    """Return all safelist IPs from US region in the form of a set."""
    return set(_get_webhooks_ips("us"))


def get_eu_safelist() -> set[str]:
    """Return all safelist IPs from EU region in the form of a set."""
    return set(_get_webhooks_ips("eu"))


def console_output() -> int:
    """Display results to console."""
    cli = {"us": get_us_safelist, "eu": get_eu_safelist}
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    result = cli.get(arg, get_all_safelist)()
    print("\n".join(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(console_output())
