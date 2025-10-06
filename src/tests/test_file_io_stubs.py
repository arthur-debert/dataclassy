"""Test the file I/O method stubs."""

import pytest
from dataclassy import dataclassy


def test_from_path_not_implemented():
    """Test that from_path raises NotImplementedError for now."""
    @dataclassy
    class Config:
        value: int
    
    with pytest.raises(ImportError):
        # Should fail because FormatHandler doesn't exist yet
        Config.from_path("config.json")


def test_to_path_not_implemented():
    """Test that to_path raises NotImplementedError for now."""
    @dataclassy
    class Config:
        value: int
    
    config = Config(42)
    
    with pytest.raises(ImportError):
        # Should fail because FormatHandler doesn't exist yet
        config.to_path("output.json")