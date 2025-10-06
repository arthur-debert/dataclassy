# Dataclassy Technical Design Document

## Motivation

Python's `dataclasses` module revolutionized how we write data containers, but real-world applications often need more:
- Converting between dictionaries and dataclasses for APIs and databases
- Loading/saving configuration from files
- Validating field values beyond type hints
- Managing environment variables and config cascading
- Preserving comments in configuration files

Dataclassy addresses these needs while maintaining 100% compatibility with standard dataclasses.

## Goals

1. **Zero Breaking Changes**: Any code using `@dataclass` should work identically with `@dataclassy`
2. **Progressive Enhancement**: Features are opt-in, not forced
3. **Type Safety**: Full type hint support with runtime validation
4. **Minimal Dependencies**: Core has zero dependencies, formats are optional
5. **Developer Experience**: Clear errors, intuitive APIs, good documentation

## Design Principles

### 1. Decorator Composition
Instead of reimplementing dataclass functionality, we wrap it:
```python
def dataclassy(cls):
    # First apply standard dataclass
    cls = dataclass(cls)
    # Then add our enhancements
    cls.from_dict = classmethod(from_dict)
    cls.to_dict = to_dict
    return cls
```

### 2. Descriptor-based Validation
Field validators are implemented as Python descriptors:
```python
class Validator:
    def __set_name__(self, owner, name):
        self.name = name
        self._attr = f'_{name}'
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._attr)
    
    def __set__(self, instance, value):
        validated = self.validate(value)
        setattr(instance, self._attr, validated)
```

### 3. Type-Aware Serialization
The serialization system uses type hints to guide conversion:
```python
def from_dict(cls, data: dict):
    type_hints = get_type_hints(cls)
    for field_name, field_type in type_hints.items():
        if is_dataclass(field_type):
            # Recursive conversion
            data[field_name] = field_type.from_dict(data[field_name])
```

### 4. Configuration Cascading
Settings decorator implements a priority system:
1. Default values in class definition
2. Config files (in order specified)
3. Environment variables
4. Runtime overrides

## Architecture

### Core Module Structure

```
src/dataclassy/
├── __init__.py          # Public API exports
├── core.py              # @dataclassy decorator
├── settings.py          # @settings decorator
├── fields/
│   ├── __init__.py
│   ├── validators.py    # Base Validator class
│   ├── color.py         # Color field type
│   └── path.py          # Path field type
├── serialization/
│   ├── __init__.py
│   ├── converter.py     # to_dict/from_dict logic
│   └── formats.py       # File format handlers
└── utils.py             # Shared utilities
```

### Key Components

#### 1. Enhanced Dataclass Decorator
- Wraps standard `@dataclass`
- Adds serialization methods
- Handles post-init validation
- Manages enum conversions

#### 2. Field Validation System
- **Base Validator**: Abstract descriptor for custom fields
- **Color Field**: Validates hex codes, RGB tuples, named colors
- **Path Field**: File system validation with existence checks

#### 3. Serialization Engine
- **Type Introspection**: Uses `get_type_hints()` for accurate types
- **Recursive Handling**: Nested dataclasses, lists, dicts
- **Union Support**: Optional types, multiple valid types
- **Custom Converters**: Enum string conversion, Path objects

#### 4. Settings Management
- **File Discovery**: Auto-finds config files by name
- **Format Detection**: JSON, YAML, TOML, INI support
- **Environment Variables**: Type-aware parsing with prefixes
- **Deep Merging**: Intelligent config combination

#### 5. Format Handlers
- **Pluggable System**: Easy to add new formats
- **Comment Preservation**: Format-specific comment handling
- **Error Recovery**: Graceful handling of malformed files

## Implementation Details

### Type Conversion Strategy

The library performs type conversion at multiple levels:

1. **Field Assignment**: Validators convert on `__set__`
2. **Dictionary Loading**: `from_dict` converts based on type hints
3. **Environment Variables**: Smart parsing for complex types
4. **File Loading**: Format-specific conversions

### Error Handling Philosophy

- **Fail Fast**: Invalid data raises immediately
- **Clear Messages**: Errors indicate field name and expected type
- **Type Safety**: No silent conversions that lose data
- **Validation Errors**: Collected and reported together

### Performance Considerations

1. **Lazy Loading**: Config files only read when needed
2. **Cached Parsing**: Parsed config data stored once
3. **Minimal Overhead**: Decorators add negligible runtime cost
4. **Optional Features**: Unused features have zero cost

### Extensibility Points

1. **Custom Validators**: Subclass `Validator` for new field types
2. **Format Handlers**: Register new file formats
3. **Type Converters**: Add handlers for custom types
4. **Merge Strategies**: Customize config merging behavior

## Testing Strategy

### Unit Tests
- Each module has dedicated test file
- Parametrized tests for edge cases
- Mock external dependencies

### Integration Tests
- Full workflow tests (create, save, load)
- Multi-format round-trip tests
- Environment variable integration

### Property Tests
- Serialization round-trip properties
- Type conversion consistency
- Merge operation properties

## Security Considerations

1. **Path Validation**: Prevents directory traversal
2. **Environment Variables**: No automatic execution
3. **File Parsing**: Safe parsing, no eval()
4. **Type Safety**: Prevents injection via type confusion

## Future Enhancements

1. **Schema Generation**: Export JSON Schema from dataclasses
2. **Async Support**: Async file operations and validation
3. **CLI Generation**: Convert dataclasses to Click commands
4. **Performance Mode**: Optional caching and optimization
5. **Plugin System**: Third-party validators and formats

## Conclusion

Dataclassy achieves its goal of enhancing dataclasses without breaking compatibility. The architecture is modular, extensible, and maintains Python's philosophy of "there should be one obvious way to do it" while adding practical features for real-world applications.