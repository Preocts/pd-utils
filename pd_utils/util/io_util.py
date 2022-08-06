from __future__ import annotations

import csv
from io import StringIO
from typing import Any
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

    @staticmethod
    def csv_to_dict(csv_string: str) -> list[dict[str, Any]]:
        """Convert a csv string to a list of dictionaries."""
        csv_io = StringIO(csv_string)
        dict_reader = csv.DictReader(csv_io)
        return [row for row in dict_reader]

    @staticmethod
    def write_to_file(filepath: str, content: str) -> None:
        """Write string to filename/path. Empty strings are ignored."""
        if not content:
            return
        with open(filepath, "w", encoding="utf-8") as outfile:
            outfile.write(content)

    @staticmethod
    def read_from_file(filepath: str) -> str:
        """Read string from filename/path. File must exist."""
        with open(filepath, encoding="utf-8") as infile:
            return infile.read()
