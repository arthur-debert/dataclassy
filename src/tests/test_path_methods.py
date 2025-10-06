"""Tests for from_path/to_path methods on dataclassy classes."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from dataclassy import dataclassy


@dataclassy
class Config:
    name: str
    value: int
    debug: bool = False


def test_from_path_to_path_json():
    """Test from_path/to_path methods with JSON."""
    config = Config(name="test", value=42, debug=True)
    
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"
        
        # Use to_path method
        config.to_path(path)
        
        # Verify file exists and contains correct data
        assert path.exists()
        data = json.loads(path.read_text())
        assert data == {"name": "test", "value": 42, "debug": True}
        
        # Use from_path method
        loaded = Config.from_path(path)
        
        assert loaded.name == "test"
        assert loaded.value == 42
        assert loaded.debug is True


def test_from_path_to_path_string_path():
    """Test that from_path/to_path accept string paths."""
    config = Config(name="test", value=123)
    
    with TemporaryDirectory() as tmpdir:
        # Test with string path
        str_path = str(Path(tmpdir) / "config.json")
        
        config.to_path(str_path)
        loaded = Config.from_path(str_path)
        
        assert loaded.name == "test"
        assert loaded.value == 123
        assert loaded.debug is False  # Default value


def test_from_path_error_handling():
    """Test from_path error handling."""
    with TemporaryDirectory() as tmpdir:
        # Non-existent file
        path = Path(tmpdir) / "missing.json"
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            Config.from_path(path)
        
        # Invalid format
        bad_path = Path(tmpdir) / "bad.xml"
        bad_path.write_text("<xml>invalid</xml>")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            Config.from_path(bad_path)


def test_to_path_creates_directories():
    """Test that to_path creates parent directories."""
    config = Config(name="test", value=42)
    
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nested" / "dirs" / "config.json"
        
        # Parent doesn't exist
        assert not path.parent.exists()
        
        # to_path should create it
        config.to_path(path)
        
        assert path.exists()
        assert Config.from_path(path).name == "test"


def test_nested_dataclasses_with_paths():
    """Test from_path/to_path with nested dataclasses."""
    @dataclassy
    class Database:
        host: str
        port: int
        
    @dataclassy
    class AppConfig:
        name: str
        database: Database
        
    config = AppConfig(
        name="myapp",
        database=Database(host="localhost", port=5432)
    )
    
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "app.json"
        
        config.to_path(path)
        loaded = AppConfig.from_path(path)
        
        assert loaded.name == "myapp"
        assert loaded.database.host == "localhost"
        assert loaded.database.port == 5432


def test_to_path_kwargs():
    """Test passing kwargs to to_path."""
    config = Config(name="test", value=42)
    
    with TemporaryDirectory() as tmpdir:
        # Test custom indentation
        path = Path(tmpdir) / "formatted.json"
        
        # Note: to_path doesn't currently support kwargs
        # This test documents current behavior
        config.to_path(path)
        
        content = path.read_text()
        # Default is 2-space indent
        assert "  " in content


def test_ini_format_with_methods():
    """Test from_path/to_path with INI format."""
    config = Config(name="myconfig", value=999, debug=True)
    
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.ini"
        
        config.to_path(path)
        
        # Check INI content
        content = path.read_text()
        assert "[DEFAULT]" in content
        assert "name = myconfig" in content
        
        # Load back
        loaded = Config.from_path(path)
        assert loaded.name == "myconfig"
        assert loaded.value == 999
        assert loaded.debug is True