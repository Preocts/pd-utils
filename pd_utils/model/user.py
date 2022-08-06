from __future__ import annotations

import dataclasses
from typing import Any

from pd_utils.model.base import Base


@dataclasses.dataclass
class User(Base):
    """Empty User object for User Report."""

    name: str = ""
    html_url: str = ""
    email: str = ""
    title: str = ""
    base_role: str = ""
    timezone: str = ""
    observer_in: list[str] | None = None
    responder_in: list[str] | None = None
    manager_in: list[str] | None = None
    has_email: bool = False
    has_push: bool = False
    has_sms: bool = False
    has_phone: bool = False
    has_blocked: bool = False
    high_urgency_email_delay: list[str] | None = None
    high_urgency_push_delay: list[str] | None = None
    high_urgency_sms_delay: list[str] | None = None
    high_urgency_phone_delay: list[str] | None = None
    low_urgency_email_delay: list[str] | None = None
    low_urgency_push_delay: list[str] | None = None
    low_urgency_sms_delay: list[str] | None = None
    low_urgency_phone_delay: list[str] | None = None

    @classmethod
    def build_from(cls, resp: dict[str, Any]) -> User:
        """Build a User object from PagerDuty API response."""
        cmethods = [cm["type"] for cm in resp["contact_methods"] or []]
        blocked = any([cm.get("blacklisted", False) for cm in resp["contact_methods"]])
        nr = "notification_rules"
        return cls(
            name=resp["name"],
            html_url=resp["html_url"],
            email=resp["email"],
            title=resp["job_title"],
            base_role=resp["role"],
            timezone=resp["time_zone"],
            observer_in=User._get_teams(resp["teams"], "observer"),
            responder_in=User._get_teams(resp["teams"], "responder"),
            manager_in=User._get_teams(resp["teams"], "manager"),
            has_email="email_contact_method" in cmethods,
            has_push="push_notification_contact_method" in cmethods,
            has_sms="sms_contact_method" in cmethods,
            has_phone="phone_contact_method" in cmethods,
            has_blocked=blocked,
            high_urgency_email_delay=User._get_delay(resp[nr], "email", "high"),
            high_urgency_push_delay=User._get_delay(resp[nr], "push", "high"),
            high_urgency_sms_delay=User._get_delay(resp[nr], "sms", "high"),
            high_urgency_phone_delay=User._get_delay(resp[nr], "phone", "high"),
            low_urgency_email_delay=User._get_delay(resp[nr], "email", "low"),
            low_urgency_push_delay=User._get_delay(resp[nr], "push", "low"),
            low_urgency_sms_delay=User._get_delay(resp[nr], "sms", "low"),
            low_urgency_phone_delay=User._get_delay(resp[nr], "phone", "low"),
        )

    @staticmethod
    def _get_teams(teams: list[dict[str, Any]], role: str) -> list[str] | None:
        """Return team names of teams with matching role."""
        return [team["name"] for team in teams if team["default_role"] == role] or None

    @staticmethod
    def _get_delay(
        nrules: list[dict[str, Any]],
        type_: str,
        urgency: str,
    ) -> list[str] | None:
        """Return delay times in minutes for given notification types."""
        delays = [
            str(nr["start_delay_in_minutes"])
            for nr in nrules
            if type_ in nr["contact_method"]["type"] and urgency == nr["urgency"]
        ]
        return delays or None
