from __future__ import annotations

import csv
from io import StringIO
from typing import Sequence

from pd_utils.model.base import Base


class IOUtil:
    @staticmethod
    def to_csv_string(objs: Sequence[Base], fieldnames: list[str] | None = None) -> str:
        """
        Convert an object to a CSV. All attributes are included by default

        Args:
            objs: Sequence of Base objects to convert
            fieldsnames: Optionally define which keys are used, extra will be ignored
        """
        csv_file = StringIO()
        if not fieldnames:
            fieldnames = list(objs[0].as_dict().keys())
        dict_writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        dict_writer.writeheader()
        dict_writer.writerows([row.as_dict() for row in objs])

        return csv_file.getvalue()
