"""Tests for the settings decorator."""

import json
import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from dataclassy import settings


def test_basic_settings():
    """Test basic settings decorator functionality."""

    @settings
    class Config:
        """Application configuration."""

        debug: bool = False
        host: str = "localhost"
        port: int = 8000

    # Create instance normally
    config = Config(debug=True, host="0.0.0.0", port=9000)
    assert config.debug is True
    assert config.host == "0.0.0.0"
    assert config.port == 9000

    # Has settings methods
    assert hasattr(Config, "load_config")
    assert hasattr(config, "reload")
    assert hasattr(config, "save_config")


def test_load_from_json():
    """Test loading configuration from JSON file."""

    @settings(config_name="app", auto_load=False)
    class AppConfig:
        debug: bool = False
        database_url: str = "sqlite:///default.db"
        timeout: int = 30

    with TemporaryDirectory() as tmpdir:
        # Create config file
        config_path = Path(tmpdir) / "app.json"
        config_path.write_text(
            json.dumps(
                {
                    "debug": True,
                    "database_url": "postgres://localhost/myapp",
                    "timeout": 60,
                }
            )
        )

        # Load config
        config = AppConfig.load_config([config_path])

        assert config.debug is True
        assert config.database_url == "postgres://localhost/myapp"
        assert config.timeout == 60


def test_environment_variables():
    """Test loading from environment variables."""

    @settings(env_prefix="MYAPP_", auto_load=False)
    class AppConfig:
        debug: bool = False
        port: int = 8000
        api_key: str = "default"

    # Set environment variables
    os.environ["MYAPP_DEBUG"] = "true"
    os.environ["MYAPP_PORT"] = "9090"
    os.environ["MYAPP_API_KEY"] = "secret123"

    try:
        config = AppConfig.load_config()

        assert config.debug is True
        assert config.port == 9090
        assert config.api_key == "secret123"
    finally:
        # Cleanup
        del os.environ["MYAPP_DEBUG"]
        del os.environ["MYAPP_PORT"]
        del os.environ["MYAPP_API_KEY"]


def test_config_cascading():
    """Test configuration cascading with merge."""

    @settings(auto_load=False)
    class Config:
        name: str = "app"
        debug: bool = False
        database: dict = None

    with TemporaryDirectory() as tmpdir:
        # Create default config
        default_config = Path(tmpdir) / "default.json"
        default_config.write_text(
            json.dumps(
                {
                    "name": "myapp",
                    "debug": False,
                    "database": {
                        "host": "localhost",
                        "port": 5432,
                        "name": "myapp_db",
                    },
                }
            )
        )

        # Create user config (overrides some values)
        user_config = Path(tmpdir) / "user.json"
        user_config.write_text(
            json.dumps({"debug": True, "database": {"host": "db.example.com"}})
        )

        # Load with cascading
        config = Config.load_config([default_config, user_config])

        assert config.name == "myapp"  # From default
        assert config.debug is True  # Overridden by user
        assert config.database["host"] == "db.example.com"  # Overridden
        assert config.database["port"] == 5432  # From default
        assert config.database["name"] == "myapp_db"  # From default


def test_auto_search_config_files():
    """Test automatic config file search."""
    with TemporaryDirectory() as tmpdir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:

            @settings(config_name="settings", auto_load=False)
            class Settings:
                app_name: str = "default"
                version: str = "1.0.0"

            # Create config file in current directory - use JSON since YAML might not be installed
            config_path = Path("settings.json")
            config_path.write_text('{"app_name": "MyApp", "version": "2.0.0"}')

            # Load should find it automatically
            config = Settings.load_config()

            assert config.app_name == "MyApp"
            assert config.version == "2.0.0"
        finally:
            os.chdir(original_cwd)


def test_save_config():
    """Test saving configuration to file."""

    @settings
    class Config:
        """Test configuration."""

        name: str = "test"
        enabled: bool = True
        count: int = 42

    config = Config(name="mytest", enabled=False, count=100)

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "saved.json"

        config.save_config(save_path)

        # Verify saved content
        saved_data = json.loads(save_path.read_text())
        assert saved_data["name"] == "mytest"
        assert saved_data["enabled"] is False
        assert saved_data["count"] == 100


def test_save_without_defaults():
    """Test saving only non-default values."""

    @settings
    class Config:
        name: str = "default_name"
        port: int = 8000
        custom_value: str = "custom"

    # Only change one value
    config = Config(name="default_name", port=9000, custom_value="custom")

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "minimal.json"

        config.save_config(
            save_path, include_defaults=False, include_comments=False
        )

        # Should only save the changed value
        saved_data = json.loads(save_path.read_text())
        assert "name" not in saved_data  # Same as default
        assert saved_data["port"] == 9000  # Changed
        assert "custom_value" not in saved_data  # Same as default


def test_reload_config():
    """Test reloading configuration."""

    @settings(auto_load=False)
    class Config:
        value: int = 0

    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_path.write_text('{"value": 10}')

        # Load initially
        Config._settings_config["config_paths"] = [config_path]
        config = Config.load_config()
        assert config.value == 10

        # Change the file
        config_path.write_text('{"value": 20}')

        # Reload
        config.reload()
        assert config.value == 20


def test_nested_environment_variables():
    """Test nested field support with environment variables."""

    @settings(env_prefix="APP_", env_nested_delimiter="__", auto_load=False)
    class Config:
        debug: bool = False
        database_host: str = "localhost"
        database_port: int = 5432

    os.environ["APP_DEBUG"] = "true"
    os.environ["APP_DATABASE_HOST"] = "db.example.com"
    os.environ["APP_DATABASE_PORT"] = "3306"

    try:
        config = Config.load_config()

        assert config.debug is True
        assert config.database_host == "db.example.com"
        assert config.database_port == 3306
    finally:
        del os.environ["APP_DEBUG"]
        del os.environ["APP_DATABASE_HOST"]
        del os.environ["APP_DATABASE_PORT"]


def test_override_values():
    """Test overriding values in load_config."""

    @settings(auto_load=False)
    class Config:
        name: str = "default"
        port: int = 8000

    # Load with overrides
    config = Config.load_config(port=9999, name="overridden")

    assert config.name == "overridden"
    assert config.port == 9999


def test_auto_load_empty_init():
    """Test auto-load when creating instance with no arguments."""

    @settings(auto_load=True, env_prefix="TEST_")
    class AutoConfig:
        value: str = "default"

    os.environ["TEST_VALUE"] = "from_env"

    try:
        # Creating with no args should auto-load
        config = AutoConfig()
        assert config.value == "from_env"

        # Creating with args should use them
        config2 = AutoConfig(value="explicit")
        assert config2.value == "explicit"
    finally:
        del os.environ["TEST_VALUE"]


def test_multiple_format_support():
    """Test loading from different file formats."""

    @settings(auto_load=False)
    class Config:
        format_type: str = "unknown"
        value: int = 0

    with TemporaryDirectory() as tmpdir:
        # Test JSON
        json_path = Path(tmpdir) / "config.json"
        json_path.write_text('{"format_type": "json", "value": 1}')

        config = Config.load_config([json_path])
        assert config.format_type == "json"
        assert config.value == 1

        # Test INI
        ini_path = Path(tmpdir) / "config.ini"
        ini_path.write_text("[DEFAULT]\nformat_type = ini\nvalue = 2\n")

        config = Config.load_config([ini_path])
        assert config.format_type == "ini"
        assert config.value == 2


def test_comment_preservation():
    """Test that docstrings are preserved as comments."""

    @settings
    class ConfigWithDocs:
        """This is the main configuration."""

        debug: bool = False
        port: int = 8000

    config = ConfigWithDocs()

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "with_comments.json"
        config.save_config(save_path, include_comments=True)

        # Check that comment was added
        saved_text = save_path.read_text()
        saved_data = json.loads(saved_text)
        assert "_comment" in saved_data
        assert saved_data["_comment"] == "This is the main configuration."
