"""Test improved bool conversion in from_dict."""

import pytest
from dataclassy import dataclassy


def test_bool_string_conversion():
    """Test that bool conversion from strings works as expected."""
    
    @dataclassy
    class Config:
        debug: bool
        verbose: bool
        enabled: bool
        active: bool
    
    # Test various true values
    data = {
        "debug": "true",
        "verbose": "1",
        "enabled": "yes", 
        "active": "on"
    }
    config = Config.from_dict(data)
    assert config.debug is True
    assert config.verbose is True
    assert config.enabled is True
    assert config.active is True
    
    # Test various false values
    data2 = {
        "debug": "false",
        "verbose": "0",
        "enabled": "no",
        "active": "off"
    }
    config2 = Config.from_dict(data2)
    assert config2.debug is False
    assert config2.verbose is False
    assert config2.enabled is False
    assert config2.active is False
    
    # Test case insensitive
    data3 = {
        "debug": "TRUE",
        "verbose": "FALSE",
        "enabled": "Yes",
        "active": "NO"
    }
    config3 = Config.from_dict(data3)
    assert config3.debug is True
    assert config3.verbose is False
    assert config3.enabled is True
    assert config3.active is False


def test_bool_invalid_string():
    """Test that invalid bool strings fail as expected."""
    
    @dataclassy
    class Config:
        flag: bool
    
    # Invalid string should not convert
    data = {"flag": "maybe"}
    result = Config.from_dict(data)
    # Should keep original value when conversion fails
    assert result.flag == "maybe"
    
    # Empty string should also fail
    data2 = {"flag": ""}
    result2 = Config.from_dict(data2)
    assert result2.flag == ""


def test_bool_non_string_conversion():
    """Test bool conversion from non-string types."""
    
    @dataclassy
    class Config:
        flag: bool
    
    # Integer conversion
    assert Config.from_dict({"flag": 1}).flag is True
    assert Config.from_dict({"flag": 0}).flag is False
    assert Config.from_dict({"flag": -1}).flag is True
    
    # None
    assert Config.from_dict({"flag": None}).flag is None
    
    # Lists (truthy/falsy)
    assert Config.from_dict({"flag": [1, 2, 3]}).flag is True
    assert Config.from_dict({"flag": []}).flag is False