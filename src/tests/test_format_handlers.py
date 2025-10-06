"""Tests for file format handlers."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from dataclassy import dataclassy
from dataclassy.serialization.formats import FormatHandler


@dataclassy
class SimpleConfig:
    name: str
    value: int
    enabled: bool = True


@dataclassy
class NestedConfig:
    database: SimpleConfig
    cache: SimpleConfig
    timeout: int = 30


def test_json_round_trip():
    """Test saving and loading JSON files."""
    config = SimpleConfig(name="test", value=42, enabled=False)

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"

        # Save to JSON
        FormatHandler.to_path(config, path)

        # Verify file exists
        assert path.exists()

        # Load from JSON
        loaded = FormatHandler.from_path(SimpleConfig, path)

        # Verify data
        assert loaded.name == "test"
        assert loaded.value == 42
        assert loaded.enabled is False


def test_json_with_nested():
    """Test JSON with nested dataclasses."""
    config = NestedConfig(
        database=SimpleConfig(name="postgres", value=5432),
        cache=SimpleConfig(name="redis", value=6379),
        timeout=60,
    )

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nested.json"

        FormatHandler.to_path(config, path)
        loaded = FormatHandler.from_path(NestedConfig, path)

        assert loaded.database.name == "postgres"
        assert loaded.database.value == 5432
        assert loaded.cache.name == "redis"
        assert loaded.cache.value == 6379
        assert loaded.timeout == 60


def test_json_formatting_options():
    """Test JSON formatting options."""
    config = SimpleConfig(name="test", value=42)

    with TemporaryDirectory() as tmpdir:
        # Test with custom indentation
        path_indent = Path(tmpdir) / "indent.json"
        FormatHandler.to_path(config, path_indent, indent=4)

        content = path_indent.read_text()
        assert "    " in content  # 4-space indent

        # Test with no indentation
        path_compact = Path(tmpdir) / "compact.json"
        FormatHandler.to_path(config, path_compact, indent=None)

        content_compact = path_compact.read_text()
        assert "\n" not in content_compact.strip()  # Single line


def test_yaml_round_trip():
    """Test saving and loading YAML files."""
    pytest.importorskip("yaml")

    config = SimpleConfig(name="test", value=42, enabled=True)

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.yaml"

        FormatHandler.to_path(config, path)
        loaded = FormatHandler.from_path(SimpleConfig, path)

        assert loaded.name == "test"
        assert loaded.value == 42
        assert loaded.enabled is True


def test_toml_round_trip():
    """Test saving and loading TOML files."""
    pytest.importorskip("tomli_w")

    config = SimpleConfig(name="test", value=42, enabled=False)

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.toml"

        FormatHandler.to_path(config, path)
        loaded = FormatHandler.from_path(SimpleConfig, path)

        assert loaded.name == "test"
        assert loaded.value == 42
        assert loaded.enabled is False


def test_ini_round_trip_single_section():
    """Test INI files with single section."""
    config = SimpleConfig(name="test", value=42, enabled=True)

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.ini"

        FormatHandler.to_path(config, path)

        # Verify INI structure
        content = path.read_text()
        assert "[DEFAULT]" in content
        assert "name = test" in content
        assert "value = 42" in content

        # Load back
        loaded = FormatHandler.from_path(SimpleConfig, path)

        assert loaded.name == "test"
        assert loaded.value == 42
        assert loaded.enabled is True


def test_ini_round_trip_multi_section():
    """Test INI files with multiple sections."""
    config = NestedConfig(
        database=SimpleConfig(name="postgres", value=5432),
        cache=SimpleConfig(name="redis", value=6379),
    )

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "multi.ini"

        FormatHandler.to_path(config, path)

        # Verify INI structure
        content = path.read_text()
        assert "[database]" in content
        assert "[cache]" in content

        # Load back
        loaded = FormatHandler.from_path(NestedConfig, path)

        assert loaded.database.name == "postgres"
        assert loaded.database.value == 5432
        assert loaded.cache.name == "redis"
        assert loaded.cache.value == 6379


def test_auto_create_parent_directory():
    """Test that parent directories are created automatically."""
    config = SimpleConfig(name="test", value=42)

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "subdir" / "nested" / "config.json"

        # Parent directories don't exist
        assert not path.parent.exists()

        # Save should create them
        FormatHandler.to_path(config, path)

        assert path.exists()
        assert path.parent.exists()


def test_file_not_found_error():
    """Test error when loading non-existent file."""
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "missing.json"

        with pytest.raises(FileNotFoundError, match="File not found"):
            FormatHandler.from_path(SimpleConfig, path)


def test_unsupported_format_error():
    """Test error for unsupported file formats."""
    config = SimpleConfig(name="test", value=42)

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.xml"

        with pytest.raises(ValueError, match="Unsupported file format: .xml"):
            FormatHandler.to_path(config, path)

        # Create a dummy file to test loading
        path.write_text("<xml></xml>")

        with pytest.raises(ValueError, match="Unsupported file format: .xml"):
            FormatHandler.from_path(SimpleConfig, path)


def test_missing_yaml_library():
    """Test error when PyYAML is not installed."""
    import sys

    # Temporarily hide yaml module
    yaml_module = sys.modules.get("yaml")
    if yaml_module:
        sys.modules["yaml"] = None

    try:
        config = SimpleConfig(name="test", value=42)

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yaml"

            with pytest.raises(ImportError, match="PyYAML is required"):
                FormatHandler.to_path(config, path)

            # Create dummy file
            path.write_text("name: test\nvalue: 42\n")

            with pytest.raises(ImportError, match="PyYAML is required"):
                FormatHandler.from_path(SimpleConfig, path)

    finally:
        # Restore yaml module
        if yaml_module:
            sys.modules["yaml"] = yaml_module


def test_missing_toml_library():
    """Test error when tomli-w is not installed."""
    import sys

    # Temporarily hide toml modules
    tomli_w_module = sys.modules.get("tomli_w")
    if tomli_w_module:
        sys.modules["tomli_w"] = None

    try:
        config = SimpleConfig(name="test", value=42)

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"

            with pytest.raises(ImportError, match="tomli-w is required"):
                FormatHandler.to_path(config, path)

    finally:
        # Restore module
        if tomli_w_module:
            sys.modules["tomli_w"] = tomli_w_module


def test_path_accepts_string():
    """Test that path parameter accepts both str and Path."""
    config = SimpleConfig(name="test", value=42)

    with TemporaryDirectory() as tmpdir:
        # Test with string path
        str_path = str(Path(tmpdir) / "string.json")
        FormatHandler.to_path(config, str_path)
        loaded = FormatHandler.from_path(SimpleConfig, str_path)

        assert loaded.name == "test"
        assert loaded.value == 42

        # Test with Path object
        path_obj = Path(tmpdir) / "path.json"
        FormatHandler.to_path(config, path_obj)
        loaded2 = FormatHandler.from_path(SimpleConfig, path_obj)

        assert loaded2.name == "test"
        assert loaded2.value == 42


def test_json_preserves_types():
    """Test that JSON preserves basic types correctly."""

    @dataclassy
    class TypedConfig:
        int_val: int
        float_val: float
        str_val: str
        bool_val: bool
        list_val: list
        dict_val: dict

    config = TypedConfig(
        int_val=42,
        float_val=3.14,
        str_val="hello",
        bool_val=True,
        list_val=[1, 2, 3],
        dict_val={"a": 1, "b": 2},
    )

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "types.json"

        FormatHandler.to_path(config, path)
        loaded = FormatHandler.from_path(TypedConfig, path)

        assert loaded.int_val == 42
        assert loaded.float_val == 3.14
        assert loaded.str_val == "hello"
        assert loaded.bool_val is True
        assert loaded.list_val == [1, 2, 3]
        assert loaded.dict_val == {"a": 1, "b": 2}

        # Verify types
        assert isinstance(loaded.int_val, int)
        assert isinstance(loaded.float_val, float)
        assert isinstance(loaded.str_val, str)
        assert isinstance(loaded.bool_val, bool)
        assert isinstance(loaded.list_val, list)
        assert isinstance(loaded.dict_val, dict)
