from __future__ import annotations

from dataclasses import dataclass

import pytest

from pd_utils.model.base import Base
from pd_utils.util import IOUtil


@dataclass
class MockModel(Base):
    name: str
    number: int
    flag: bool


@pytest.fixture
def mockmodel() -> tuple[list[MockModel], str]:
    sample = [
        MockModel(name="Test1", number=1, flag=True),
        MockModel(name="Test2", number=2, flag=False),
        MockModel(name="Test3", number=3, flag=True),
        MockModel(name="Test4", number=4, flag=False),
    ]
    expected = (
        "name,number,flag\r\n"
        "Test1,1,True\r\n"
        "Test2,2,False\r\n"
        "Test3,3,True\r\n"
        "Test4,4,False\r\n"
    )

    return sample, expected


def test_to_csv_string(mockmodel: tuple[list[MockModel], str]) -> None:
    sample, expected = mockmodel
    result = IOUtil.to_csv_string(sample)
    assert result == expected


def test_to_csv_string_cstm_fieldnames(mockmodel: tuple[list[MockModel], str]) -> None:
    sample, expected = mockmodel
    expected = (
        "flag,name\r\n"
        "True,Test1\r\n"
        "False,Test2\r\n"
        "True,Test3\r\n"
        "False,Test4\r\n"
    )
    result = IOUtil.to_csv_string(sample, ["flag", "name"])
    assert result == expected
