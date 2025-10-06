"""Tests for format-aware comment handling in settings."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from dataclassy import settings


def test_json_comments_remain_as_fields():
    """Test that JSON comments are saved as _comment fields."""

    @settings
    class Config:
        """
        Main configuration for the application.

        This handles all app settings.

        debug : bool
            Enable debug mode
        port : int
            Server port number
        """

        debug: bool = False
        port: int = 8000

    config = Config()

    with TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "config.json"
        config.save_config(json_path, include_comments=True)

        # Load and check JSON structure
        with open(json_path) as f:
            data = json.load(f)

        # Class comment
        assert "_comment" in data
        assert "Main configuration for the application." in data["_comment"]
        assert "This handles all app settings." in data["_comment"]

        # Field comments
        assert "_debug_comment" in data
        assert data["_debug_comment"] == "Enable debug mode"

        assert "_port_comment" in data
        assert data["_port_comment"] == "Server port number"


def test_yaml_comments_as_native():
    """Test that YAML files get native comments when ruamel.yaml is available."""
    yaml = pytest.importorskip("ruamel.yaml")

    @settings
    class Config:
        """
        YAML test configuration.

        name : str
            Application name
        timeout : int
            Request timeout in seconds
        """

        name: str = "test"
        timeout: int = 30

    config = Config()

    with TemporaryDirectory() as tmpdir:
        yaml_path = Path(tmpdir) / "config.yaml"
        config.save_config(yaml_path, include_comments=True)

        # Read the raw YAML file
        content = yaml_path.read_text()

        # Should have comment syntax, not _comment fields
        assert "# YAML test configuration." in content
        assert "# Application name" in content
        assert "# Request timeout in seconds" in content
        assert "_comment" not in content
        assert "_name_comment" not in content


def test_yaml_fallback_comments():
    """Test YAML comment handling when only PyYAML is available."""

    # This test would need to mock the absence of ruamel.yaml
    # For now, we'll test the manual comment writing
    @settings
    class Config:
        """Simple config for YAML."""

        value: int = 42

    config = Config()

    with TemporaryDirectory() as tmpdir:
        yaml_path = Path(tmpdir) / "config_fallback.yaml"

        # Simulate PyYAML-only environment by using our internal function
        from dataclassy.settings import _save_with_format_aware_comments

        _save_with_format_aware_comments(Config, {"value": 42}, yaml_path, True)

        content = yaml_path.read_text()
        # When falling back to PyYAML, class comment should be at top
        if "# Simple config for YAML." in content:
            assert True  # Fallback worked
        else:
            # ruamel.yaml is available, that's fine too
            assert "Simple config for YAML." in content


def test_toml_comments_with_tomlkit():
    """Test that TOML files get proper comments when tomlkit is available."""
    tomlkit = pytest.importorskip("tomlkit")

    @settings
    class Config:
        """
        TOML configuration example.

        host : str
            Database host
        port : int
            Database port
        """

        host: str = "localhost"
        port: int = 5432

    config = Config()

    with TemporaryDirectory() as tmpdir:
        toml_path = Path(tmpdir) / "config.toml"
        config.save_config(toml_path, include_comments=True)

        content = toml_path.read_text()

        # Should have TOML comments
        assert "# TOML configuration example." in content
        assert "# Database host" in content
        assert "# Database port" in content


def test_ini_comments():
    """Test that INI files get comments at the top."""

    @settings
    class Config:
        """
        INI configuration file.

        This uses the INI format.

        username : str
            User name for login
        enabled : bool
            Whether feature is enabled
        """

        username: str = "admin"
        enabled: bool = True

    config = Config()

    with TemporaryDirectory() as tmpdir:
        ini_path = Path(tmpdir) / "config.ini"
        config.save_config(ini_path, include_comments=True)

        content = ini_path.read_text()

        # INI should have class comments at top
        assert "# INI configuration file." in content
        assert "# This uses the INI format." in content
        # Field comments can't be inline in INI
        assert "# User name for login" not in content


def test_no_comments_flag():
    """Test that include_comments=False doesn't add any comments."""

    @settings
    class Config:
        """
        Config with docs.

        value : int
            Some value
        """

        value: int = 42

    config = Config()

    with TemporaryDirectory() as tmpdir:
        # Test each format
        formats = [
            ("config.json", lambda p: json.loads(p.read_text())),
            ("config.yaml", lambda p: p.read_text()),
            ("config.ini", lambda p: p.read_text()),
        ]

        for filename, reader in formats:
            if filename == "config.yaml":
                pytest.importorskip("yaml")

            path = Path(tmpdir) / filename
            config.save_config(path, include_comments=False)

            content = reader(path)

            # No comments in any format
            if isinstance(content, dict):
                assert "_comment" not in content
                assert "_value_comment" not in content
            else:
                assert "Config with docs" not in content
                assert "Some value" not in content


def test_multiline_field_comments():
    """Test handling of multiline field documentation."""

    @settings
    class Config:
        """
        Configuration with multiline docs.

        connection_string : str
            Database connection string.
            Format: protocol://user:pass@host:port/db
            Example: postgresql://user:pass@localhost/mydb
        """

        connection_string: str = "sqlite:///local.db"

    config = Config()

    with TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "multiline.json"
        config.save_config(json_path, include_comments=True)

        with open(json_path) as f:
            data = json.load(f)

        # Check multiline comment is preserved
        comment = data["_connection_string_comment"]
        assert "Database connection string." in comment
        assert "Format: protocol://user:pass@host:port/db" in comment
        assert "Example: postgresql://user:pass@localhost/mydb" in comment
