"""Tests for enhanced environment variable type coercion in settings."""

import os
from typing import List, Dict, Optional
from tempfile import TemporaryDirectory
from pathlib import Path

from dataclassy import settings


def test_env_list_basic():
    """Test basic list type coercion from environment variables."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        tags: List[str] = field(default_factory=list)
        ports: List[int] = field(default_factory=list)

    # Set environment variables
    os.environ["TEST_TAGS"] = "prod,staging,dev"
    os.environ["TEST_PORTS"] = "8080,8081,8082"

    try:
        config = Config.load_config()
        assert config.tags == ["prod", "staging", "dev"]
        assert config.ports == [8080, 8081, 8082]
    finally:
        del os.environ["TEST_TAGS"]
        del os.environ["TEST_PORTS"]


def test_env_list_with_spaces():
    """Test list parsing handles spaces correctly."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        items: List[str] = field(default_factory=list)

    os.environ["TEST_ITEMS"] = "item 1, item 2 , item 3"

    try:
        config = Config.load_config()
        assert config.items == ["item 1", "item 2", "item 3"]
    finally:
        del os.environ["TEST_ITEMS"]


def test_env_list_typed():
    """Test list with specific element types."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        numbers: List[float] = field(default_factory=list)
        flags: List[bool] = field(default_factory=list)

    os.environ["TEST_NUMBERS"] = "1.5,2.7,3.14"
    os.environ["TEST_FLAGS"] = "true,false,yes,no"

    try:
        config = Config.load_config()
        assert config.numbers == [1.5, 2.7, 3.14]
        assert config.flags == [True, False, True, False]
    finally:
        del os.environ["TEST_NUMBERS"]
        del os.environ["TEST_FLAGS"]


def test_env_dict_key_value_pairs():
    """Test dict parsing from key=value pairs."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        headers: Dict[str, str] = field(default_factory=dict)
        settings: Dict[str, int] = field(default_factory=dict)

    os.environ["TEST_HEADERS"] = (
        "Content-Type=application/json,Authorization=Bearer token"
    )
    os.environ["TEST_SETTINGS"] = "timeout=30,retries=3,max_connections=100"

    try:
        config = Config.load_config()
        assert config.headers == {
            "Content-Type": "application/json",
            "Authorization": "Bearer token",
        }
        assert config.settings == {
            "timeout": 30,
            "retries": 3,
            "max_connections": 100,
        }
    finally:
        del os.environ["TEST_HEADERS"]
        del os.environ["TEST_SETTINGS"]


def test_env_dict_json_format():
    """Test dict parsing from JSON format."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        metadata: Dict[str, any] = field(default_factory=dict)

    os.environ["TEST_METADATA"] = (
        '{"version": "1.0", "debug": true, "count": 42}'
    )

    try:
        config = Config.load_config()
        assert config.metadata == {"version": "1.0", "debug": True, "count": 42}
    finally:
        del os.environ["TEST_METADATA"]


def test_env_dict_typed_values():
    """Test dict with typed values."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        scores: Dict[str, float] = field(default_factory=dict)
        flags: Dict[str, bool] = field(default_factory=dict)

    os.environ["TEST_SCORES"] = "math=95.5,science=87.3,english=91.0"
    os.environ["TEST_FLAGS"] = "feature_a=true,feature_b=false,feature_c=yes"

    try:
        config = Config.load_config()
        assert config.scores == {"math": 95.5, "science": 87.3, "english": 91.0}
        assert config.flags == {
            "feature_a": True,
            "feature_b": False,
            "feature_c": True,
        }
    finally:
        del os.environ["TEST_SCORES"]
        del os.environ["TEST_FLAGS"]


def test_env_optional_types():
    """Test Optional type handling."""

    @settings(env_prefix="TEST_")
    class Config:
        name: Optional[str] = None
        port: Optional[int] = None
        items: Optional[List[str]] = None

    # Test with values
    os.environ["TEST_NAME"] = "myapp"
    os.environ["TEST_PORT"] = "8080"
    os.environ["TEST_ITEMS"] = "a,b,c"

    try:
        config = Config.load_config()
        assert config.name == "myapp"
        assert config.port == 8080
        assert config.items == ["a", "b", "c"]
    finally:
        del os.environ["TEST_NAME"]
        del os.environ["TEST_PORT"]
        del os.environ["TEST_ITEMS"]

    # Test with null values
    os.environ["TEST_NAME"] = "none"
    os.environ["TEST_PORT"] = "null"
    os.environ["TEST_ITEMS"] = ""

    try:
        config = Config.load_config()
        assert config.name is None
        assert config.port is None
        assert config.items == []  # Empty list for empty string
    finally:
        del os.environ["TEST_NAME"]
        del os.environ["TEST_PORT"]
        del os.environ["TEST_ITEMS"]


def test_env_empty_collections():
    """Test empty list and dict handling."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        tags: List[str] = field(default_factory=lambda: ["default"])
        metadata: Dict[str, str] = field(
            default_factory=lambda: {"default": "value"}
        )

    # Empty values should create empty collections
    os.environ["TEST_TAGS"] = ""
    os.environ["TEST_METADATA"] = ""

    try:
        config = Config.load_config()
        assert config.tags == []
        assert config.metadata == {}
    finally:
        del os.environ["TEST_TAGS"]
        del os.environ["TEST_METADATA"]


def test_env_complex_nested():
    """Test complex nested scenarios."""
    from dataclasses import field

    @settings(env_prefix="APP_")
    class Config:
        servers: List[str] = field(default_factory=list)
        ports: List[int] = field(default_factory=list)
        features: Dict[str, bool] = field(default_factory=dict)
        limits: Dict[str, int] = field(default_factory=dict)
        admin_email: Optional[str] = None

    # Set all environment variables
    os.environ["APP_SERVERS"] = (
        "api.example.com,web.example.com,admin.example.com"
    )
    os.environ["APP_PORTS"] = "8080,8081,8082"
    os.environ["APP_FEATURES"] = "auth=true,logging=true,caching=false"
    os.environ["APP_LIMITS"] = "max_requests=1000,timeout=30,retries=3"
    os.environ["APP_ADMIN_EMAIL"] = "admin@example.com"

    try:
        config = Config.load_config()

        assert config.servers == [
            "api.example.com",
            "web.example.com",
            "admin.example.com",
        ]
        assert config.ports == [8080, 8081, 8082]
        assert config.features == {
            "auth": True,
            "logging": True,
            "caching": False,
        }
        assert config.limits == {
            "max_requests": 1000,
            "timeout": 30,
            "retries": 3,
        }
        assert config.admin_email == "admin@example.com"

        # Save and verify round-trip
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config.save_config(config_path)

            # Load from file (not env vars this time)
            loaded = Config.load_config(
                config_paths=[config_path], load_env=False
            )
            assert loaded.servers == config.servers
            assert loaded.features == config.features
    finally:
        for key in [
            "APP_SERVERS",
            "APP_PORTS",
            "APP_FEATURES",
            "APP_LIMITS",
            "APP_ADMIN_EMAIL",
        ]:
            if key in os.environ:
                del os.environ[key]


def test_env_invalid_conversions():
    """Test that invalid conversions are handled gracefully."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        port: int = 8080
        ratio: float = 1.0
        items: List[int] = field(default_factory=list)

    # Set invalid values
    os.environ["TEST_PORT"] = "not_a_number"
    os.environ["TEST_RATIO"] = "invalid"
    os.environ["TEST_ITEMS"] = "1,2,not_a_number,4"

    try:
        config = Config.load_config()
        # Invalid values should be skipped, defaults used
        assert config.port == 8080
        assert config.ratio == 1.0
        # For lists, individual items might fail
        # Our implementation will fail on the whole list if any item fails
        assert config.items == []  # Default when conversion fails
    finally:
        del os.environ["TEST_PORT"]
        del os.environ["TEST_RATIO"]
        del os.environ["TEST_ITEMS"]


def test_env_dict_with_equals_in_value():
    """Test dict parsing when values contain equals signs."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        connection_strings: Dict[str, str] = field(default_factory=dict)

    os.environ["TEST_CONNECTION_STRINGS"] = (
        "db=host=localhost;port=5432,cache=redis://localhost:6379"
    )

    try:
        config = Config.load_config()
        assert config.connection_strings == {
            "db": "host=localhost;port=5432",
            "cache": "redis://localhost:6379",
        }
    finally:
        del os.environ["TEST_CONNECTION_STRINGS"]


def test_env_list_single_item():
    """Test list with single item (no comma)."""
    from dataclasses import field

    @settings(env_prefix="TEST_")
    class Config:
        tags: List[str] = field(default_factory=list)

    os.environ["TEST_TAGS"] = "production"

    try:
        config = Config.load_config()
        assert config.tags == ["production"]
    finally:
        del os.environ["TEST_TAGS"]


def test_env_integration_with_file_config():
    """Test that env vars properly override file config."""
    from dataclasses import field

    @settings(env_prefix="TEST_", config_name="app")
    class Config:
        name: str = "default"
        items: List[str] = field(default_factory=list)
        settings: Dict[str, int] = field(default_factory=dict)

    with TemporaryDirectory() as tmpdir:
        # Create config file
        config_path = Path(tmpdir) / "app.json"
        import json

        with open(config_path, "w") as f:
            json.dump(
                {
                    "name": "from_file",
                    "items": ["file_item1", "file_item2"],
                    "settings": {"file_setting": 10},
                },
                f,
            )

        # Set env vars that should override
        os.environ["TEST_NAME"] = "from_env"
        os.environ["TEST_ITEMS"] = "env_item1,env_item2,env_item3"
        os.environ["TEST_SETTINGS"] = "env_setting=20,other=30"

        try:
            # Change to tmpdir to find config file
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            config = Config.load_config()

            # Env vars should override file values
            assert config.name == "from_env"
            assert config.items == ["env_item1", "env_item2", "env_item3"]
            assert config.settings == {"env_setting": 20, "other": 30}
        finally:
            os.chdir(original_cwd)
            del os.environ["TEST_NAME"]
            del os.environ["TEST_ITEMS"]
            del os.environ["TEST_SETTINGS"]
