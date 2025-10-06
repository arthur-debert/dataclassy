"""Test edge cases for type conversion with strict validation."""

import pytest
from dataclassy import dataclassy


def test_invalid_numeric_conversions():
    """Test that invalid numeric conversions raise errors."""
    
    @dataclassy
    class NumericConfig:
        count: int
        ratio: float
    
    # Invalid int conversion
    with pytest.raises(TypeError) as exc_info:
        NumericConfig.from_dict({"count": "123.45", "ratio": 1.0})
    assert "Field 'count' expects int" in str(exc_info.value)
    
    # Invalid float conversion
    with pytest.raises(TypeError) as exc_info:
        NumericConfig.from_dict({"count": 123, "ratio": "not-a-number"})
    assert "Field 'ratio' expects float" in str(exc_info.value)
    
    # Complex objects
    with pytest.raises(TypeError) as exc_info:
        NumericConfig.from_dict({"count": [1, 2, 3], "ratio": 1.0})
    assert "Field 'count' expects int" in str(exc_info.value)


def test_string_always_converts():
    """Test that string type accepts any value via str()."""
    
    @dataclassy
    class StringConfig:
        value: str
    
    # All these should work
    assert StringConfig.from_dict({"value": 123}).value == "123"
    assert StringConfig.from_dict({"value": True}).value == "True"
    assert StringConfig.from_dict({"value": 3.14}).value == "3.14"
    assert StringConfig.from_dict({"value": [1, 2]}).value == "[1, 2]"
    assert StringConfig.from_dict({"value": {"key": "val"}}).value == "{'key': 'val'}"


def test_empty_string_edge_cases():
    """Test empty string conversion edge cases."""
    
    @dataclassy
    class EdgeCaseConfig:
        text: str
        flag: bool
    
    # Empty string to str should work
    config = EdgeCaseConfig.from_dict({"text": "", "flag": True})
    assert config.text == ""
    
    # Empty string to bool should fail
    with pytest.raises(TypeError) as exc_info:
        EdgeCaseConfig.from_dict({"text": "test", "flag": ""})
    assert "Field 'flag' expects bool" in str(exc_info.value)