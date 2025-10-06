# Dataclassy

Enhanced dataclasses for Python with validation, serialization, and configuration management.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

Dataclassy is a lightweight library that extends Python's built-in `dataclasses` with:

- 🚀 **100% dataclass compatible** - Drop-in replacement, all dataclass features work
- 🔄 **Enhanced serialization** - Automatic conversion to/from dicts with proper type handling
- ✅ **Field validation** - Built-in validators for common types (Color, Path, etc.)
- 📁 **File I/O** - Load/save from JSON, YAML, TOML, and INI formats
- ⚙️ **Configuration management** - Advanced settings with environment variables and cascading
- 🎨 **Smart type conversion** - Automatic enum conversion, nested dataclass handling
- 📝 **Comment preservation** - Keep documentation in your config files

## Installation

```bash
pip install dataclassy
```

For additional format support:

```bash
pip install dataclassy[yaml]  # For YAML support
pip install dataclassy[toml]  # For TOML support
pip install dataclassy[all]   # For all optional dependencies
```

## Quick Start

### Basic Usage

```python
from dataclassy import dataclassy

@dataclassy
class Person:
    name: str
    age: int
    email: str = ""

# Create from dict
person = Person.from_dict({"name": "Alice", "age": 30})

# Convert to dict
data = person.to_dict()

# Save to file
person.to_path("person.json")

# Load from file
person2 = Person.from_path("person.json")
```

### Field Validation

```python
from dataclassy import dataclassy, Color, Path

@dataclassy
class Theme:
    name: str
    primary: Color = Color()  # Accepts hex, RGB tuples, or color names
    logo: Path = Path(must_exist=True, extensions=[".png", ".jpg"])

# Color field accepts multiple formats
theme = Theme(name="Ocean", primary="navy", logo="./assets/logo.png")
print(theme.primary)  # "#000080"
# Access color methods through the descriptor
print(Theme.primary.to_rgb(theme))  # (0, 0, 128)
print(Theme.primary.to_css(theme))  # "rgb(0, 0, 128)"
```

### Settings Management

```python
from dataclassy import settings, field
from typing import List, Dict

@settings(env_prefix="MYAPP_", config_name="config")
class AppConfig:
    """
    Application configuration.
    
    debug : bool
        Enable debug mode for verbose logging
    database_url : str
        PostgreSQL connection string
    port : int
        Server port number
    tags : List[str]
        Feature tags (comma-separated in env vars)
    limits : Dict[str, int]
        Rate limits per endpoint
    """
    debug: bool = False
    database_url: str = "sqlite:///app.db"
    port: int = 8000
    tags: List[str] = field(default_factory=list)
    limits: Dict[str, int] = field(default_factory=dict)

# Automatically loads from:
# 1. config.json/yaml/toml in current directory
# 2. Environment variables with type conversion:
#    - MYAPP_DEBUG=true
#    - MYAPP_PORT=8080
#    - MYAPP_TAGS=auth,api,v2  (becomes ["auth", "api", "v2"])
#    - MYAPP_LIMITS=api=100,web=50  (becomes {"api": 100, "web": 50})
# 3. Override with code
config = AppConfig()  # Auto-loads config files and env vars (when auto_load=True, the default)

# Save with comments
config.save_config("config.json", include_comments=True)
```

## Advanced Features

### Nested Dataclasses

```python
@dataclassy
class Database:
    host: str
    port: int
    
@dataclassy
class Config:
    name: str
    database: Database
    
# from_dict handles nested structures automatically
config = Config.from_dict({
    "name": "myapp",
    "database": {"host": "localhost", "port": 5432}
})
```

### Enum Support

```python
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"

@dataclassy
class Task:
    title: str
    status: Status

# Accepts enum values or strings
task1 = Task(title="Deploy", status=Status.ACTIVE)
task2 = Task(title="Test", status="pending")  # Auto-converts to Status.PENDING
```

### Path Field with Auto-Loading

```python
@dataclassy
class ConfigFile:
    path: Path = Path(
        must_exist=True,
        extensions=[".json"],
        parse_callback=lambda p: json.loads(p.read_text())
    )

config = ConfigFile(path="./settings.json")
# Automatically loads and parses the file
print(config._path_data)  # Parsed JSON content (stored as _{field_name}_data)
```

### Configuration Cascading

```python
@settings(config_paths=["default.json", "user.json"], env_prefix="APP_")
class Settings:
    name: str = "app"
    debug: bool = False
    features: dict = None

# Loads and merges in order:
# 1. default.json
# 2. user.json (overrides default)
# 3. Environment variables (override files)
settings = Settings.load_config()
```

## API Reference

### Core Decorators

#### `@dataclassy`

Enhances a dataclass with serialization and type conversion.

```python
@dataclassy(init=True, repr=True, eq=True, ...)  # All dataclass params supported
class MyClass:
    field: type
```

#### `@settings`

Adds configuration management capabilities.

```python
@settings(
    config_paths=None,      # List of config files to load
    config_name=None,       # Base name for auto-discovery
    env_prefix=None,        # Prefix for env variables
    auto_load=True,         # Load config when instantiated with no args
)
class MyConfig:
    field: type
```

### Field Types

#### `Color`

Validates and normalizes color values.

```python
from dataclassy import Color

class MyClass:
    color: Color = Color()  # Accepts hex, RGB, color names
    
# Use in a dataclassy class
@dataclassy
class Theme:
    primary: Color = Color()
    
# The Color field validates and converts values
theme = Theme(primary="red")
print(theme.primary)  # "#ff0000"
# Access methods through the descriptor
print(Theme.primary.to_rgb(theme))  # (255, 0, 0)
print(Theme.primary.to_css(theme))  # "rgb(255, 0, 0)"
```

#### `Path`

Validates file system paths with extensive options.

```python
from dataclassy import Path

@dataclassy
class Config:
    path: Path = Path(
        must_exist=False,       # Path must exist
        is_file=None,          # Must be file (True), dir (False), or either (None)
        extensions=None,       # Allowed file extensions
        create_parents=False,  # Create parent directories
        parse_callback=None,   # Function to parse file contents
    )

# Path fields provide convenience methods
config = Config(path="./config.json")
# If parse_callback is set, parsed data is in _{field_name}_data
if hasattr(config, '_path_data'):
    print(config._path_data)
    
# Path fields also provide methods (via descriptor):
# Config.path.read_text(config)
# Config.path.write_text(config, content)
# Config.path.read_bytes(config)
```

### Methods

Every dataclassy class gets these methods:

- `from_dict(data: dict) -> Self` - Create instance from dictionary
- `to_dict() -> dict` - Convert to dictionary
- `from_path(path: str | Path) -> Self` - Load from file
- `to_path(path: str | Path)` - Save to file

Settings classes additionally get:

- `load_config(config_paths=None, load_env=True, **overrides) -> Self`
- `save_config(path, include_defaults=True, include_comments=True)`
- `reload()` - Reload configuration from sources

## Migration from dataclasses

Dataclassy is designed as a drop-in replacement:

```python
# Before
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int

# After
from dataclassy import dataclassy

@dataclassy  # Just change the decorator!
class Person:
    name: str
    age: int
    
# All existing code continues to work
# Plus you get from_dict, to_dict, etc.
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/dataclassy.git
cd dataclassy

# Install with Poetry
poetry install

# Run tests
poetry run pytest
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=dataclassy

# Run specific test file
poetry run pytest tests/test_core.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on Python's excellent `dataclasses` module
- Inspired by `pydantic`, `attrs`, and `marshmallow`
- Special thanks to the Python community
