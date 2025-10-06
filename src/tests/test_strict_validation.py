"""Test strict validation in dataclassy."""

import pytest
from enum import Enum

from dataclassy import dataclassy


class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


def test_enum_conversion_failure_raises():
    """Test that invalid enum values raise errors in __post_init__."""

    @dataclassy
    class Config:
        status: Status

    # Valid enum string should work
    config = Config("active")
    assert config.status == Status.ACTIVE

    # Invalid enum string should raise
    with pytest.raises(ValueError) as exc_info:
        Config("invalid")
    assert "Invalid value for status" in str(exc_info.value)
    assert "Cannot convert 'invalid' to Status" in str(exc_info.value)


def test_from_dict_type_validation():
    """Test that from_dict validates types properly."""

    @dataclassy
    class TypedConfig:
        count: int
        ratio: float
        name: str
        enabled: bool

    # Valid conversions
    valid_data = {
        "count": "42",
        "ratio": "3.14",
        "name": 123,  # Will convert to "123"
        "enabled": "true",
    }
    config = TypedConfig.from_dict(valid_data)
    assert config.count == 42
    assert config.ratio == 3.14
    assert config.name == "123"
    assert config.enabled is True

    # Invalid int conversion - should fail
    with pytest.raises(TypeError) as exc_info:
        TypedConfig.from_dict(
            {
                "count": "not-a-number",
                "ratio": 1.0,
                "name": "test",
                "enabled": True,
            }
        )
    assert "Field 'count' expects int" in str(exc_info.value)

    # Invalid float conversion - should fail
    with pytest.raises(TypeError) as exc_info:
        TypedConfig.from_dict(
            {
                "count": 1,
                "ratio": "not-a-float",
                "name": "test",
                "enabled": True,
            }
        )
    assert "Field 'ratio' expects float" in str(exc_info.value)

    # Invalid bool conversion - should fail
    with pytest.raises(TypeError) as exc_info:
        TypedConfig.from_dict(
            {
                "count": 1,
                "ratio": 1.0,
                "name": "test",
                "enabled": "maybe",  # Not a valid bool string
            }
        )
    assert "Field 'enabled' expects bool" in str(exc_info.value)


def test_nested_dataclass_validation():
    """Test validation in nested dataclasses."""

    @dataclassy
    class Inner:
        value: int
        status: Status

    @dataclassy
    class Outer:
        name: str
        inner: Inner

    # Valid nested data
    valid_data = {"name": "test", "inner": {"value": 42, "status": "active"}}
    outer = Outer.from_dict(valid_data)
    assert outer.inner.value == 42
    assert outer.inner.status == Status.ACTIVE

    # Invalid nested enum should raise during construction
    with pytest.raises(ValueError) as exc_info:
        Outer("test", Inner(42, "invalid"))
    assert "Invalid value for status" in str(exc_info.value)


def test_optional_field_validation():
    """Test that None values bypass validation."""

    @dataclassy
    class OptionalConfig:
        value: int
        status: Status = None

    # None should be allowed
    config = OptionalConfig(42, None)
    assert config.value == 42
    assert config.status is None

    # from_dict with None
    data = {"value": 42, "status": None}
    config2 = OptionalConfig.from_dict(data)
    assert config2.status is None


def test_list_validation_errors():
    """Test validation errors in lists."""

    @dataclassy
    class Item:
        id: int
        name: str

    @dataclassy
    class Container:
        items: list[Item]

    # Invalid item data should fail
    with pytest.raises(TypeError) as exc_info:
        Container.from_dict({"items": [{"id": "not-an-int", "name": "test"}]})
    assert "Field 'id' expects int" in str(exc_info.value)
