# Dataclassy API Reference

## Core Module

### `dataclassy.dataclassy`

```python
@dataclassy(
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    match_args: bool = True,
    kw_only: bool = False,
    slots: bool = False,
) -> Type[T]
```

Enhanced dataclass decorator that adds serialization and type conversion features while maintaining 100% compatibility with Python's built-in `dataclass`.

**Parameters:**
- All parameters are identical to `dataclasses.dataclass`
- See [Python dataclass documentation](https://docs.python.org/3/library/dataclasses.html)

**Added Methods:**
- `from_dict(cls, data: dict) -> T`: Create instance from dictionary
- `to_dict(self) -> dict`: Convert instance to dictionary
- `from_path(cls, path: str | Path) -> T`: Load instance from file
- `to_path(self, path: str | Path) -> None`: Save instance to file

**Features:**
- Automatic enum conversion (by value or name)
- Nested dataclass handling
- Type coercion with validation
- Smart handling of Optional types

### `dataclassy.settings`

```python
@settings(
    config_paths: Optional[List[Union[str, Path]]] = None,
    config_name: Optional[str] = None,
    search_dirs: Optional[List[Union[str, Path]]] = None,
    env_prefix: Optional[str] = None,
    env_nested_delimiter: str = "__",
    merge_strategy: str = "deep",
    auto_load: bool = True,
    case_sensitive: bool = False,
) -> Type[T]
```

Settings decorator for configuration management. Applies `@dataclassy` automatically.

**Parameters:**
- `config_paths`: Explicit paths to config files to load
- `config_name`: Base name for config file auto-discovery (e.g., "config" for config.json)
- `search_dirs`: Directories to search for config files (default: current directory)
- `env_prefix`: Prefix for environment variables (e.g., "MYAPP_")
- `env_nested_delimiter`: Delimiter for nested env vars (e.g., "__" for MYAPP__DB__HOST)
- `merge_strategy`: How to merge configs ("deep" or "shallow")
- `auto_load`: Whether to automatically load config when instantiated with no args
- `case_sensitive`: Whether env var names are case-sensitive

**Added Methods:**
- `load_config(config_paths=None, load_env=True, **overrides) -> T`: Load configuration
- `save_config(path, include_defaults=True, include_comments=True) -> None`: Save configuration
- `reload(self) -> None`: Reload configuration from sources

## Field Types

### `dataclassy.Color`

```python
Color() -> Color
```

Field type for color values with validation and conversion.

**Accepts:**
- Hex strings: `"#FF0000"`, `"#F00"`
- RGB tuples: `(255, 0, 0)`
- Color names: `"red"`, `"navy"`, `"darkgreen"`

**Methods:**
- `to_hex() -> str`: Get hex representation
- `to_rgb() -> Tuple[int, int, int]`: Get RGB tuple
- `to_css() -> str`: Get CSS color string

**Example:**
```python
@dataclassy
class Theme:
    primary: Color = "#3498db"
    secondary: Color = Color()  # Default: #000000

theme = Theme(primary="navy", secondary=(255, 128, 0))
```

### `dataclassy.Path`

```python
Path(
    must_exist: bool = False,
    is_file: Optional[bool] = None,
    is_dir: Optional[bool] = None,
    extensions: Optional[List[str]] = None,
    resolve: bool = True,
    expanduser: bool = True,
    create_parents: bool = False,
    parse_callback: Optional[Callable[[Path], Any]] = None,
    parsed_attr: Optional[str] = None,
    raise_parse_errors: bool = False,
) -> Path
```

Field type for file system paths with validation and auto-loading.

**Parameters:**
- `must_exist`: Whether the path must exist
- `is_file`: Must be a file (True), directory (False), or either (None)
- `is_dir`: Whether the path must be a directory
- `extensions`: Allowed file extensions (e.g., `['.txt', '.md']`)
- `resolve`: Whether to resolve to absolute path
- `expanduser`: Whether to expand `~` to user home directory
- `create_parents`: Whether to create parent directories if they don't exist
- `parse_callback`: Optional callback to parse/load file contents
- `parsed_attr`: Name of attribute to store parsed data (default: field_name + '_data')
- `raise_parse_errors`: Whether to raise exceptions from parse_callback

**Helper Methods:**
- `read_text(encoding='utf-8') -> Optional[str]`: Read file contents as text
- `read_bytes() -> Optional[bytes]`: Read file contents as bytes
- `write_text(content: str, encoding='utf-8') -> bool`: Write text to file
- `write_bytes(content: bytes) -> bool`: Write bytes to file

**Example:**
```python
@dataclassy
class Config:
    config_file: Path = Path(
        must_exist=True,
        extensions=['.json'],
        parse_callback=lambda p: json.loads(p.read_text())
    )

config = Config(config_file="./settings.json")
print(config.config_file_data)  # Parsed JSON content
```

## Serialization

### `dataclassy.serialization.Converter`

```python
class Converter:
    @staticmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Convert dictionary to dataclass instance."""
    
    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        """Convert dataclass instance to dictionary."""
```

Type-aware conversion between dictionaries and dataclass instances.

**Features:**
- Handles nested dataclasses
- Enum conversion (by value or name)
- Optional[T] type handling
- List[T] with dataclass elements
- Dict[K, V] with dataclass values
- Smart type coercion with validation

### `dataclassy.serialization.FormatHandler`

```python
class FormatHandler:
    @staticmethod
    def from_path(cls: Type[T], path: Union[str, Path]) -> T:
        """Load dataclass from file."""
    
    @staticmethod
    def to_path(obj: Any, path: Union[str, Path], **kwargs) -> None:
        """Save dataclass to file."""
```

File I/O handler supporting multiple formats.

**Supported Formats:**
- JSON (`.json`)
- YAML (`.yaml`, `.yml`) - requires PyYAML
- TOML (`.toml`) - requires tomli/tomli-w
- INI (`.ini`)

**Format Detection:**
- Automatic based on file extension
- Creates parent directories automatically

## Utilities

### `dataclassy.utils`

```python
def enum_converter(enum_class: Type[Enum]) -> Callable:
    """Create converter function for enum type."""

def merge_configs(
    base: Dict[str, Any],
    override: Dict[str, Any],
    strategy: str = "deep"
) -> Dict[str, Any]:
    """Merge two configuration dictionaries."""

def is_missing(value: Any) -> bool:
    """Check if a value is the MISSING sentinel."""
```

Utility functions used internally by dataclassy.

## Type Annotations

Dataclassy is fully type-annotated and works well with mypy and other type checkers.

```python
from typing import Optional, List, Dict
from dataclassy import dataclassy

@dataclassy
class TypedConfig:
    # All standard type hints work
    name: str
    count: int
    ratio: float
    enabled: bool
    
    # Optional types
    description: Optional[str] = None
    
    # Collections
    tags: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Nested dataclasses
    database: Optional['DatabaseConfig'] = None
```

## Exceptions

Dataclassy raises standard Python exceptions:

- `TypeError`: For type conversion failures
- `ValueError`: For validation failures
- `FileNotFoundError`: When loading from non-existent files
- `ImportError`: When optional dependencies are missing

All exceptions include informative error messages to help with debugging.