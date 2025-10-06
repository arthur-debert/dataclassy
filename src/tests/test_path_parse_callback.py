"""Tests for improved Path field parse_callback functionality."""

import json
import pytest
from pathlib import Path as PathLib
from tempfile import TemporaryDirectory

from dataclassy import dataclassy
from dataclassy.fields import Path


def test_parse_callback_basic():
    """Test basic parse_callback functionality."""

    def parse_json(path: PathLib) -> dict:
        """Parse JSON file."""
        return json.loads(path.read_text())

    @dataclassy
    class Config:
        config_file: Path = Path(parse_callback=parse_json)

    with TemporaryDirectory() as tmpdir:
        # Create a JSON file
        json_path = PathLib(tmpdir) / "config.json"
        json_path.write_text('{"key": "value", "number": 42}')

        # Create config with path
        config = Config(config_file=str(json_path))

        # Check that data was parsed and stored
        assert hasattr(config, "config_file_data")
        assert config.config_file_data == {"key": "value", "number": 42}


def test_parse_callback_custom_attr():
    """Test parse_callback with custom parsed_attr name."""

    def parse_json(path: PathLib) -> dict:
        return json.loads(path.read_text())

    @dataclassy
    class Config:
        config_file: Path = Path(
            parse_callback=parse_json, parsed_attr="config"
        )

    with TemporaryDirectory() as tmpdir:
        json_path = PathLib(tmpdir) / "config.json"
        json_path.write_text('{"setting": "enabled"}')

        config = Config(config_file=str(json_path))

        # Check custom attribute name
        assert hasattr(config, "config")
        assert config.config == {"setting": "enabled"}
        # Default name should not exist
        assert not hasattr(config, "config_file_data")


def test_parse_callback_error_handling():
    """Test parse_callback error handling."""

    def parse_strict_json(path: PathLib) -> dict:
        """Parse JSON strictly."""
        return json.loads(path.read_text())

    @dataclassy
    class ConfigSilent:
        config_file: Path = Path(
            parse_callback=parse_strict_json,
            raise_parse_errors=False,  # Default
        )

    @dataclassy
    class ConfigStrict:
        config_file: Path = Path(
            parse_callback=parse_strict_json, raise_parse_errors=True
        )

    with TemporaryDirectory() as tmpdir:
        # Create invalid JSON file
        bad_json = PathLib(tmpdir) / "bad.json"
        bad_json.write_text("{invalid json}")

        # Silent mode: stores None on error
        config_silent = ConfigSilent(config_file=str(bad_json))
        assert hasattr(config_silent, "config_file_data")
        assert config_silent.config_file_data is None

        # Strict mode: raises error
        with pytest.raises(ValueError, match="Failed to parse config_file"):
            ConfigStrict(config_file=str(bad_json))


def test_parse_callback_only_on_files():
    """Test that parse_callback only runs on files, not directories."""
    call_count = 0

    def counting_parser(path: PathLib) -> str:
        nonlocal call_count
        call_count += 1
        return "parsed"

    @dataclassy
    class Config:
        path: Path = Path(parse_callback=counting_parser)

    with TemporaryDirectory() as tmpdir:
        # Test with directory - should not call parser
        config = Config(path=tmpdir)
        assert call_count == 0
        assert not hasattr(config, "path_data")

        # Test with file - should call parser
        file_path = PathLib(tmpdir) / "file.txt"
        file_path.write_text("content")

        config.path = str(file_path)
        assert call_count == 1
        assert config.path_data == "parsed"


def test_parse_callback_on_change():
    """Test that parse_callback runs when path changes."""
    parse_calls = []

    def tracking_parser(path: PathLib) -> dict:
        content = json.loads(path.read_text())
        parse_calls.append(content)
        return content

    @dataclassy
    class Config:
        config_file: Path = Path(parse_callback=tracking_parser)

    with TemporaryDirectory() as tmpdir:
        # First file
        json1 = PathLib(tmpdir) / "config1.json"
        json1.write_text('{"version": 1}')

        config = Config(config_file=str(json1))
        assert len(parse_calls) == 1
        assert config.config_file_data == {"version": 1}

        # Change to second file
        json2 = PathLib(tmpdir) / "config2.json"
        json2.write_text('{"version": 2}')

        config.config_file = str(json2)
        assert len(parse_calls) == 2
        assert config.config_file_data == {"version": 2}


def test_parse_callback_with_validation():
    """Test parse_callback with path validation."""

    def parse_json(path: PathLib) -> dict:
        return json.loads(path.read_text())

    @dataclassy
    class Config:
        config_file: Path = Path(
            must_exist=True, extensions=[".json"], parse_callback=parse_json
        )

    with TemporaryDirectory() as tmpdir:
        # Test with valid JSON file
        json_path = PathLib(tmpdir) / "config.json"
        json_path.write_text('{"valid": true}')

        config = Config(config_file=str(json_path))
        assert config.config_file_data == {"valid": True}

        # Test with non-existent file - should fail validation before parsing
        with pytest.raises(ValueError, match="does not exist"):
            Config(config_file=str(PathLib(tmpdir) / "missing.json"))

        # Test with wrong extension - should fail validation
        txt_path = PathLib(tmpdir) / "config.txt"
        txt_path.write_text('{"wrong": "extension"}')

        with pytest.raises(ValueError, match="must have extension"):
            Config(config_file=str(txt_path))
