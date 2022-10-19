from __future__ import annotations

from dataclasses import dataclass

import pytest
from pd_utils.model.base import Base
from pd_utils.util import ioutil


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
    result = ioutil.to_csv_string(sample)
    assert result == expected


def test_to_csv_string_empty() -> None:
    result = ioutil.to_csv_string([])

    assert result == ""


def test_to_csv_string_cstm_fieldnames(mockmodel: tuple[list[MockModel], str]) -> None:
    sample, expected = mockmodel
    expected = (
        "flag,name\r\n"
        "True,Test1\r\n"
        "False,Test2\r\n"
        "True,Test3\r\n"
        "False,Test4\r\n"
    )
    result = ioutil.to_csv_string(sample, ["flag", "name"])
    assert result == expected


def test_write_to_file_empty_file_does_nothing() -> None:
    # This will fail if an emtpy string is not early exited
    ioutil.write_to_file("", "")


def test_write_to_file(mock_filename: str) -> None:
    content = "This is a test."

    ioutil.write_to_file(mock_filename, content)

    with open(mock_filename) as infile:
        verify = infile.read()

    assert verify == content


def test_read_from_file(mock_filename: str) -> None:
    content = "This is a test."
    with open(mock_filename, "w") as outfile:
        outfile.write(content)

    verify = ioutil.read_from_file(mock_filename)

    assert verify == content


def test_csv_to_dict() -> None:
    content = "name,value\r\ntest1,1\r\ntest2,2\r\n"
    expected = [
        {"name": "test1", "value": "1"},
        {"name": "test2", "value": "2"},
    ]

    result = ioutil.csv_to_dict(content)

    assert result == expected
