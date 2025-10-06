# Dataclassy Vision Document (Original Design)

## Overview

Dataclassy is a lightweight enhancement library for Python's dataclasses that maintains 100% compatibility while adding practical features for real-world data handling. The library follows a philosophy of zero learning curve - if you know dataclasses, you already know dataclassy.

## Core Design Principles

1. **100% Dataclass Compatible**: Every dataclassy is a valid dataclass that can be used anywhere a dataclass is expected
2. **Zero Runtime Overhead**: Validation and conversion happen once at construction time via `__post_init__`
3. **Type Safety**: Preserves all type hints and static analysis capabilities
4. **Composable**: Features can be mixed and matched as needed
5. **Fail Fast**: Invalid data raises clear exceptions at construction time

## Architecture

### Module Structure

```
dataclassy/
├── __init__.py          # Public API exports
├── core.py              # Main @dataclassy decorator
├── fields/              # Field type library
│   ├── __init__.py      
│   ├── validators.py    # Base Validator descriptor
│   ├── color.py         # Color field type
│   └── path.py          # Path field type  
├── serialization/       # Serialization functionality
│   ├── __init__.py
│   ├── converter.py     # Type-aware conversion engine
│   └── formats.py       # File format handlers
├── settings.py          # @settings decorator
├── integrations/
│   └── click.py         # Click CLI integration
└── utils.py             # Shared utilities
```

### Core Components

#### 1. The @dataclassy Decorator

The main decorator is a thin wrapper around `@dataclass` that adds:
- Automatic enum string conversion in `__post_init__`
- Serialization methods: `from_dict()`, `to_dict()`, `from_path()`, `to_path()`
- Support for custom field validators via descriptors

```python
@dataclassy
class Config:
    host: str
    port: int = 8080
    log_level: LogLevel = LogLevel.INFO  # Enum - accepts strings too
```

#### 2. Field Type System

Custom field types use Python's descriptor protocol for reusable validation:

```python
class Validator:
    """Base validator using descriptor protocol"""
    def __set_name__(self, owner, name):
        self.private_name = '_' + name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)
    
    def __set__(self, obj, value):
        value = self.convert(value)  # Type conversion
        self.validate(value)          # Validation
        setattr(obj, self.private_name, value)
```

Field types include:
- **Color**: Accepts hex strings, RGB tuples, and named colors
- **Path**: File system paths with validation, auto-loading, and format restrictions

#### 3. Serialization System

The serialization system provides intelligent conversion between dictionaries and dataclasses:

- **from_dict()**: Recursively converts dictionaries to dataclasses with:
  - Nested dataclass support
  - Enum string matching (by value or name)
  - Optional/Union type handling
  - List[T] and Dict[K,V] with nested dataclasses
  - Missing field handling via defaults

- **from_path()/to_path()**: File I/O with automatic format detection:
  - JSON, YAML, TOML, INI support
  - Comment preservation using docstrings
  - Format auto-detection by file extension

#### 4. @settings Decorator

Enhanced decorator for configuration management:
- Cascading configuration file loading
- Environment variable override support
- Deep merging of nested configurations
- Docstring-based comment generation in output files

```python
@settings(env_prefix="APP_", config_paths=["default.yaml", "user.yaml"])
@dataclassy
class AppConfig:
    """Application configuration"""
    
    host: str = "localhost"
    """Server hostname"""
    
    port: int = 8080
    """Server port number"""
```

#### 5. Click Integration

Automatic CLI generation from dataclasses:
- Fields become CLI options
- Enums become choice parameters
- Bool fields become flags
- Metadata provides help text

## Implementation Strategy

### Notes on Final Implementation vs Original Vision

The final implementation closely followed the original vision with some notable enhancements and adjustments:

#### Enhancements Beyond Original Plan:
1. **Format-aware Comment System**: The implementation went beyond simple JSON comments to provide native comment support for YAML (via ruamel.yaml) and TOML (via tomlkit), making config files more readable and maintainable.

2. **Advanced Environment Variable Coercion**: The env var system now supports complex types like List[str] and Dict[str, int], parsing comma-separated values and key=value pairs intelligently.

3. **Path Field Improvements**: Added convenient methods like read_text(), write_text(), and read_bytes() directly on Path fields, making file operations more ergonomic.

4. **Better Error Handling**: Instead of silent failures, the library now provides informative exceptions with clear messages about what went wrong.

5. **Recursive Type Conversion**: The from_dict() method handles deeply nested structures with proper type conversion at all levels.

#### Divergences from Original Plan:
1. **Color Field API**: The original design implied color methods would be on the value itself (theme.primary.to_rgb()), but the implementation uses descriptors, requiring Theme.primary.to_rgb(theme).

2. **Parsed Data Storage**: Path fields with parse_callback store data as _{field_name}_data instead of {field_name}_data to avoid conflicts.

3. **Click Integration**: Postponed to a future release to focus on core functionality and ensure a solid foundation.

4. **Import Strategy**: Uses explicit imports from dataclasses module rather than wrapping everything, ensuring better compatibility and clearer dependencies.

#### Key Design Decisions Validated:
- 100% dataclass compatibility maintained throughout
- Zero learning curve achieved - existing dataclass code just works
- All features are opt-in with sensible defaults
- Clean separation between core functionality and optional features
- Minimal dependencies with extras for format support

## Implementation Strategy

### Phase 1: Core Foundation
1. Base `@dataclassy` decorator with dataclass wrapping
2. Serialization mixin methods
3. Basic enum conversion in `__post_init__`

### Phase 2: Field Types
1. Base `Validator` descriptor class
2. `Color` field implementation
3. `Path` field implementation

### Phase 3: Serialization Engine
1. Type-aware `from_dict()` converter
2. Format handlers for JSON/YAML/TOML/INI
3. Comment preservation system

### Phase 4: Advanced Features
1. `@settings` decorator with config merging
2. Environment variable loading
3. Click integration utilities

### Phase 5: Testing & Polish
1. Comprehensive test suite
2. Type stub files for mypy
3. Documentation and examples

## Technical Decisions

### Why Descriptors for Field Types?

Descriptors provide the cleanest way to add validation without modifying dataclass internals:
- Work with frozen dataclasses
- Validate on every assignment, not just construction
- Reusable across multiple dataclasses
- No performance overhead for fields that don't need validation

### Why Generate __init__ Instead of __post_init__?

We use `__post_init__` for conversions rather than generating a custom `__init__` because:
- Maintains 100% dataclass compatibility
- Preserves all dataclass features (fields, defaults, etc.)
- Simpler implementation with less magic
- Clear separation of concerns

### Handling Circular References

The library explicitly does not handle circular references in serialization:
- Matches standard `asdict()` behavior
- Keeps implementation simple
- Circular data structures are rare in configuration/data transfer use cases

## Usage Examples

### Basic Usage

```python
from dataclassy import dataclassy, Color, Path

@dataclassy
class Theme:
    name: str
    primary_color: Color = "#3498db"
    icon_path: Path = Path("./icons", is_dir=True)

# Create from dict with type conversion
theme = Theme.from_dict({
    "name": "Ocean",
    "primary_color": "blue",  # Named color converted to hex
    "icon_path": "./assets/icons"  # String converted to Path
})

# Save with comments
theme.to_path("theme.yaml")
```

### Configuration Management

```python
@settings(env_prefix="MYAPP_")
@dataclassy 
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    
@settings(config_paths=["config/default.yaml", "config/local.yaml"])
@dataclassy
class AppConfig:
    database: DatabaseConfig
    debug: bool = False

# Loads from files, then env vars, then kwargs
config = AppConfig(debug=True)
```

### CLI Integration

```python
from dataclassy.integrations.click import dataclass_command

cli = dataclass_command(AppConfig)
# Automatically generates CLI with all options
```

## Performance Considerations

1. **Construction Time**: All validation happens in `__post_init__`, adding minimal overhead
2. **No Runtime Introspection**: Unlike some validation libraries, we don't inspect types at runtime
3. **Descriptor Access**: Field types using descriptors have standard attribute access performance
4. **Serialization**: `from_dict()` is optimized for common cases (primitives, dataclasses, enums)

## Future Extensions

Possible future enhancements that maintain the lightweight philosophy:
- Additional field types (Email, URL, IPAddress)
- Async file I/O support
- Schema generation for OpenAPI/JSON Schema
- Integration with other CLI libraries (Typer, Fire)