"""Edge case tests for dataclassy with parametrized inputs."""

import pytest
from enum import Enum
from typing import List, Optional, Dict, Union
from dataclasses import field, FrozenInstanceError

from dataclassy import dataclassy, field as dc_field
from dataclassy.utils import enum_converter, merge_configs, is_missing, MISSING


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class IntEnum(Enum):
    ONE = 1
    TWO = 2
    THREE = 3


@pytest.mark.parametrize("input_value,expected", [
    # Enum instance passes through
    (Color.RED, Color.RED),
    # String value matching
    ("red", Color.RED),
    ("green", Color.GREEN),
    # Case-insensitive name matching
    ("RED", Color.RED),
    ("Red", Color.RED),
    ("rEd", Color.RED),
    # Integer enum
    (1, IntEnum.ONE),
    ("ONE", IntEnum.ONE),
    ("one", IntEnum.ONE),
])
def test_enum_converter_valid_inputs(input_value, expected):
    """Test enum converter with various valid inputs."""
    if expected.__class__ == Color:
        converter = enum_converter(Color)
    else:
        converter = enum_converter(IntEnum)
    
    result = converter(input_value)
    assert result == expected


@pytest.mark.parametrize("enum_class,input_value,error_msg", [
    (Color, "yellow", "Cannot convert 'yellow' to Color"),
    (Color, 42, "Cannot convert '42' to Color"),
    (IntEnum, 5, "Cannot convert '5' to IntEnum"),
    (IntEnum, "FOUR", "Cannot convert 'FOUR' to IntEnum"),
    (Color, None, "Cannot convert 'None' to Color"),
    (Color, [], "Cannot convert '\\[\\]' to Color"),
])
def test_enum_converter_invalid_inputs(enum_class, input_value, error_msg):
    """Test enum converter with invalid inputs."""
    converter = enum_converter(enum_class)
    
    with pytest.raises(ValueError, match=error_msg):
        converter(input_value)


@pytest.mark.parametrize("base,override,strategy,expected", [
    # Shallow merge
    (
        {"a": 1, "b": 2},
        {"b": 3, "c": 4},
        "shallow",
        {"a": 1, "b": 3, "c": 4}
    ),
    # Deep merge - nested dicts
    (
        {"a": {"x": 1, "y": 2}, "b": 3},
        {"a": {"y": 20, "z": 30}, "c": 4},
        "deep",
        {"a": {"x": 1, "y": 20, "z": 30}, "b": 3, "c": 4}
    ),
    # Deep merge - override non-dict with dict
    (
        {"a": 1, "b": 2},
        {"a": {"x": 10}},
        "deep",
        {"a": {"x": 10}, "b": 2}
    ),
    # Deep merge - override dict with non-dict
    (
        {"a": {"x": 1}, "b": 2},
        {"a": 42},
        "deep",
        {"a": 42, "b": 2}
    ),
    # Empty dicts
    ({}, {"a": 1}, "deep", {"a": 1}),
    ({"a": 1}, {}, "deep", {"a": 1}),
    ({}, {}, "deep", {}),
])
def test_merge_configs(base, override, strategy, expected):
    """Test config merging with various inputs."""
    result = merge_configs(base, override, strategy)
    assert result == expected


def test_is_missing():
    """Test is_missing utility function."""
    assert is_missing(MISSING) is True
    assert is_missing(None) is False
    assert is_missing(0) is False
    assert is_missing("") is False
    assert is_missing([]) is False


@pytest.mark.parametrize("data,should_pass", [
    # Non-dict inputs to from_dict
    (None, True),  # None should return None
    ([], False),   # List should fail
    ("string", False),  # String should fail
    (42, False),   # Number should fail
])
def test_from_dict_non_dict_inputs(data, should_pass):
    """Test from_dict with non-dictionary inputs."""
    @dataclassy
    class Simple:
        value: int
    
    if should_pass:
        result = Simple.from_dict(data)
        assert result is None
    else:
        with pytest.raises(Exception):  # Could be TypeError or AttributeError
            Simple.from_dict(data)


@pytest.mark.parametrize("field_type,input_value,expected_value,expected_type", [
    # String to bool edge cases - now with proper conversion
    (bool, "true", True, bool),
    (bool, "false", False, bool),
    (bool, "True", True, bool),
    (bool, "False", False, bool),
    (bool, "1", True, bool),
    (bool, "0", False, bool),
    (bool, "yes", True, bool),
    (bool, "no", False, bool),
    (bool, "on", True, bool),
    (bool, "off", False, bool),
    (bool, "", "", str),  # Empty string can't convert to bool
    # Number edge cases
    (int, "123", 123, int),
    (int, 123.0, 123, int),  # Should convert float to int
    (int, "123.45", "123.45", str),  # Invalid conversion, returns as-is
    (float, "123.45", 123.45, float),
    (float, 123, 123.0, float),
    # String edge cases
    (str, 123, "123", str),
    (str, True, "True", str),  # str(True) = "True"
    (str, None, None, type(None)),
])
def test_type_coercion_edge_cases(field_type, input_value, expected_value, expected_type):
    """Test various type coercion edge cases."""
    @dataclassy
    class TypeTest:
        value: field_type
    
    data = {"value": input_value}
    result = TypeTest.from_dict(data)
    
    assert result.value == expected_value
    assert type(result.value) == expected_type


def test_union_type_handling():
    """Test handling of Union types beyond Optional."""
    @dataclassy
    class MultiType:
        # Union of multiple types
        value: Union[int, str, bool]
        # Union with None in the middle
        optional_middle: Union[int, None, str]
        # Nested union
        nested: Union[List[int], Dict[str, str], None]
    
    # Test first type matches
    data1 = {
        "value": 42,
        "optional_middle": None,
        "nested": [1, 2, 3]
    }
    result1 = MultiType.from_dict(data1)
    assert result1.value == 42
    assert result1.optional_middle is None
    assert result1.nested == [1, 2, 3]
    
    # Test fallback to later types
    data2 = {
        "value": "hello",
        "optional_middle": "world",
        "nested": {"key": "value"}
    }
    result2 = MultiType.from_dict(data2)
    assert result2.value == "hello"
    assert result2.optional_middle == "world"
    assert result2.nested == {"key": "value"}


def test_deeply_nested_edge_cases():
    """Test edge cases in deeply nested structures."""
    @dataclassy
    class Level3:
        value: int
        optional: Optional[str] = None
    
    @dataclassy
    class Level2:
        items: List[Level3]
        mapping: Dict[str, Level3]
    
    @dataclassy
    class Level1:
        nested: Optional[Level2]
        direct: Level3
    
    # Test with None in nested structure
    data = {
        "nested": {
            "items": [
                {"value": 1, "optional": "one"},
                {"value": 2},  # optional uses default
                {"value": 3, "optional": None}
            ],
            "mapping": {
                "first": {"value": 10},
                "second": {"value": 20, "optional": "twenty"}
            }
        },
        "direct": {"value": 100}
    }
    
    result = Level1.from_dict(data)
    assert len(result.nested.items) == 3
    assert result.nested.items[0].optional == "one"
    assert result.nested.items[1].optional is None
    assert result.nested.items[2].optional is None
    assert result.nested.mapping["first"].value == 10
    assert result.nested.mapping["first"].optional is None


def test_non_dataclass_from_dict():
    """Test calling from_dict on non-dataclass returns data as-is."""
    class NotDataclass:
        pass
    
    from dataclassy.serialization.converter import Converter
    
    data = {"key": "value"}
    result = Converter.from_dict(NotDataclass, data)
    assert result == data


def test_list_without_type_args():
    """Test List without type arguments."""
    @dataclassy
    class GenericList:
        items: list  # No type args
        typed_items: List[int]
    
    data = {
        "items": [1, "two", 3.0, True],
        "typed_items": ["1", "2", "3"]  # Should convert to ints
    }
    
    result = GenericList.from_dict(data)
    assert result.items == [1, "two", 3.0, True]
    assert result.typed_items == [1, 2, 3]


def test_dict_without_type_args():
    """Test Dict without type arguments."""
    @dataclassy
    class GenericDict:
        mapping: dict  # No type args
        typed_mapping: Dict[str, int]
    
    data = {
        "mapping": {"a": 1, "b": "two", "c": [1, 2, 3]},
        "typed_mapping": {"x": "10", "y": "20"}  # Should convert values to ints
    }
    
    result = GenericDict.from_dict(data)
    assert result.mapping == {"a": 1, "b": "two", "c": [1, 2, 3]}
    assert result.typed_mapping == {"x": 10, "y": 20}


def test_slots_dataclass():
    """Test dataclassy with slots=True."""
    @dataclassy(slots=True)
    class SlottedClass:
        value: int
        name: str = "default"
    
    # Should work normally
    obj = SlottedClass(42, "test")
    assert obj.value == 42
    assert obj.name == "test"
    
    # from_dict should work
    obj2 = SlottedClass.from_dict({"value": 100})
    assert obj2.value == 100
    assert obj2.name == "default"
    
    # Should not have __dict__
    assert not hasattr(obj, '__dict__')


def test_error_handling_in_conversion():
    """Test that conversion errors are handled gracefully."""
    @dataclassy
    class ErrorTest:
        value: int
        enum_field: Color
    
    # Invalid int conversion - should keep as string
    data1 = {"value": "not-a-number", "enum_field": "red"}
    result1 = ErrorTest.from_dict(data1)
    assert result1.value == "not-a-number"
    assert result1.enum_field == Color.RED
    
    # Invalid enum conversion - should keep as string
    data2 = {"value": 42, "enum_field": "invalid-color"}
    result2 = ErrorTest.from_dict(data2)
    assert result2.value == 42
    assert result2.enum_field == "invalid-color"


def test_from_dict_with_extra_fields():
    """Test that extra fields in dict are ignored."""
    @dataclassy
    class Simple:
        a: int
        b: str
    
    data = {
        "a": 1,
        "b": "test",
        "c": "extra",  # Not in dataclass
        "d": {"nested": "extra"}  # Not in dataclass
    }
    
    result = Simple.from_dict(data)
    assert result.a == 1
    assert result.b == "test"
    assert not hasattr(result, 'c')
    assert not hasattr(result, 'd')


@pytest.mark.parametrize("frozen", [True, False])
def test_frozen_with_enum_conversion(frozen):
    """Test frozen dataclass with enum conversion."""
    @dataclassy(frozen=frozen)
    class FrozenTest:
        status: Color
        value: int = 42
    
    obj = FrozenTest("red", 100)
    assert obj.status == Color.RED
    assert obj.value == 100
    
    if frozen:
        with pytest.raises(FrozenInstanceError):
            obj.value = 200


def test_complex_type_conversion_failures():
    """Test that failed conversions don't crash but return original values."""
    @dataclassy
    class ComplexTypes:
        int_field: int
        float_field: float
        str_field: str
    
    # Complex objects that can't be converted to int/float
    data = {
        "int_field": {"nested": "dict"},
        "float_field": ["list", "of", "items"],
        "str_field": {"another": "dict"}
    }
    
    result = ComplexTypes.from_dict(data)
    # Should keep original values when conversion fails
    assert result.int_field == {"nested": "dict"}
    assert result.float_field == ["list", "of", "items"]
    assert result.str_field == "{'another': 'dict'}"  # str() of dict


def test_inheritance_with_from_dict():
    """Test from_dict with inherited dataclasses."""
    @dataclassy
    class Base:
        base_field: str
        shared: int = 1
    
    @dataclassy
    class Derived(Base):
        derived_field: str = "default_derived"
        shared: int = 2  # Override default
    
    data = {
        "base_field": "base",
        "derived_field": "derived",
        "shared": 42
    }
    
    result = Derived.from_dict(data)
    assert result.base_field == "base"
    assert result.derived_field == "derived"
    assert result.shared == 42
    
    # Test with missing fields - should use defaults
    data2 = {
        "base_field": "base"
    }
    result2 = Derived.from_dict(data2)
    assert result2.base_field == "base"
    assert result2.derived_field == "default_derived"
    assert result2.shared == 2