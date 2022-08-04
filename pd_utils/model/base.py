from __future__ import annotations

import dataclasses
import json
from typing import Any


@dataclasses.dataclass(repr=False)
class Base:
    def __str__(self) -> str:
        return self.as_json()

    def as_dict(self) -> dict[str, Any]:
        """Render object as dictionary."""
        return dataclasses.asdict(self)

    def as_json(self) -> str:
        """Render object as JSON string."""
        return json.dumps(self.as_dict())
