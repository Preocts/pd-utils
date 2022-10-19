from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class UserTeam:
    """Empty model of a User Team."""

    user_id: str = ""
    team_id: str = ""
    team_name: str = ""
    team_role: str = ""
