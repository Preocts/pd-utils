from __future__ import annotations

import dataclasses

import pytest

from pd_utils.model.base import Base


@pytest.fixture
def model() -> Base:
    @dataclasses.dataclass
    class TestClass(Base):
        test: str

    return TestClass("Test")


def test_as_dict(model: Base) -> None:
    assert model.as_dict() == {"test": "Test"}


def test_as_json(model: Base) -> None:
    assert model.as_json() == '{"test": "Test"}'


def test_str(model: Base) -> None:
    assert str(model) == '{"test": "Test"}'
