"""Tests for settings comment preservation with field-level documentation."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from dataclassy import settings


def test_field_level_documentation():
    """Test extraction of field-level documentation from docstrings."""

    @settings
    class ConfigWithFieldDocs:
        """
        Main application configuration.

        This class handles all configuration options for the application.

        debug : bool
            Enable debug mode for verbose logging
        port : int
            Server port number (must be between 1024-65535)
        database_url : str
            Connection string for the database
        """

        debug: bool = False
        port: int = 8000
        database_url: str = "sqlite:///app.db"

    config = ConfigWithFieldDocs()

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "config_with_field_docs.json"
        config.save_config(save_path, include_comments=True)

        # Check saved content
        saved_data = json.loads(save_path.read_text())

        # Should have main comment (without field docs)
        assert "_comment" in saved_data
        assert "Main application configuration" in saved_data["_comment"]
        assert "This class handles all configuration" in saved_data["_comment"]

        # Should have field comments
        assert "_debug_comment" in saved_data
        assert (
            "Enable debug mode for verbose logging"
            in saved_data["_debug_comment"]
        )

        assert "_port_comment" in saved_data
        assert (
            "Server port number (must be between 1024-65535)"
            in saved_data["_port_comment"]
        )

        assert "_database_url_comment" in saved_data
        assert (
            "Connection string for the database"
            in saved_data["_database_url_comment"]
        )


def test_simple_docstring_without_fields():
    """Test that simple docstrings work without field documentation."""

    @settings
    class SimpleConfig:
        """Simple configuration class."""

        name: str = "app"
        value: int = 42

    config = SimpleConfig()

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "simple.json"
        config.save_config(save_path, include_comments=True)

        saved_data = json.loads(save_path.read_text())

        # Should have class comment
        assert saved_data["_comment"] == "Simple configuration class."
        # Should not have field comments
        assert "_name_comment" not in saved_data
        assert "_value_comment" not in saved_data


def test_mixed_field_documentation():
    """Test docstring with some fields documented and others not."""

    @settings
    class MixedConfig:
        """
        Configuration with mixed documentation.

        name : str
            Application name
        """

        name: str = "myapp"
        version: str = "1.0.0"  # Not documented in docstring
        debug: bool = False  # Not documented in docstring

    config = MixedConfig()

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "mixed.json"
        config.save_config(save_path, include_comments=True)

        saved_data = json.loads(save_path.read_text())

        # Should have main comment
        assert "_comment" in saved_data
        assert (
            "Configuration with mixed documentation." in saved_data["_comment"]
        )

        # Should have comment for documented field
        assert "_name_comment" in saved_data
        assert "Application name" in saved_data["_name_comment"]

        # Should not have comments for undocumented fields
        assert "_version_comment" not in saved_data
        assert "_debug_comment" not in saved_data


def test_multiline_field_documentation():
    """Test field documentation that spans multiple lines."""

    @settings
    class MultilineConfig:
        """
        Configuration with multiline field docs.

        database_url : str
            Database connection string.
            Can be PostgreSQL, MySQL, or SQLite.
            Format: driver://user:pass@host/db
        timeout : int
            Request timeout in seconds.
            Default is 30 seconds.
        """

        database_url: str = "sqlite:///app.db"
        timeout: int = 30

    config = MultilineConfig()

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "multiline.json"
        config.save_config(save_path, include_comments=True)

        saved_data = json.loads(save_path.read_text())

        # Check multiline comments are preserved
        assert "_database_url_comment" in saved_data
        db_comment = saved_data["_database_url_comment"]
        assert "Database connection string." in db_comment
        assert "Can be PostgreSQL, MySQL, or SQLite." in db_comment
        assert "Format: driver://user:pass@host/db" in db_comment

        assert "_timeout_comment" in saved_data
        timeout_comment = saved_data["_timeout_comment"]
        assert "Request timeout in seconds." in timeout_comment
        assert "Default is 30 seconds." in timeout_comment


def test_no_comments_flag():
    """Test that include_comments=False doesn't add any comments."""

    @settings
    class DocConfig:
        """
        Configuration with documentation.

        value : int
            Some value
        """

        value: int = 42

    config = DocConfig()

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "no_comments.json"
        config.save_config(save_path, include_comments=False)

        saved_data = json.loads(save_path.read_text())

        # Should not have any comment fields
        assert "_comment" not in saved_data
        assert "_value_comment" not in saved_data

        # Should only have the actual data
        assert saved_data == {"value": 42}
