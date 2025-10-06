# Migration Guide

## Migrating from dataclasses to dataclassy

Dataclassy is designed as a drop-in replacement for Python's `dataclasses`. This guide helps you migrate existing code.

### Basic Migration

The simplest migration requires changing just one import:

```python
# Before
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    email: str = ""

# After
from dataclassy import dataclassy

@dataclassy  # Just change the decorator!
class Person:
    name: str
    age: int
    email: str = ""
```

**That's it!** All your existing code continues to work exactly as before, plus you get additional features.

### Using dataclassy's Re-exports

For convenience, dataclassy re-exports common dataclasses utilities:

```python
# Before
from dataclasses import dataclass, field, fields, asdict, is_dataclass

# After
from dataclassy import dataclassy, field, fields, asdict, is_dataclass
```

### Taking Advantage of New Features

Once migrated, you can start using dataclassy's enhancements:

```python
@dataclassy
class Person:
    name: str
    age: int
    email: str = ""

# New capabilities available immediately:
person = Person.from_dict({"name": "Alice", "age": 30})
person.to_path("person.json")
person2 = Person.from_path("person.json")
```

### Enum Handling

Dataclassy automatically handles enum conversion:

```python
from enum import Enum

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

# Before (with dataclass)
@dataclass
class User:
    name: str
    status: Status
    
# Would fail:
# user = User(name="Alice", status="active")  # TypeError!

# After (with dataclassy)
@dataclassy
class User:
    name: str
    status: Status
    
# Works automatically:
user = User(name="Alice", status="active")  # Converts to Status.ACTIVE
```

### Nested Dataclasses

Dataclassy handles nested structures in `from_dict`:

```python
@dataclassy
class Address:
    street: str
    city: str

@dataclassy
class Person:
    name: str
    address: Address

# Works automatically:
person = Person.from_dict({
    "name": "Alice",
    "address": {"street": "123 Main St", "city": "NYC"}
})
```

### Configuration Classes

Transform configuration classes using `@settings`:

```python
# Before
@dataclass
class Config:
    debug: bool = False
    port: int = 8000
    
config = Config()  # Manual loading needed

# After
from dataclassy import settings

@settings(env_prefix="APP_", config_name="config")
class Config:
    debug: bool = False
    port: int = 8000
    
config = Config()  # Auto-loads from files and env vars!
```

## Common Patterns

### Pattern 1: Loading Configuration

```python
# Old way
import json
from dataclasses import dataclass

@dataclass
class Config:
    host: str
    port: int

# Manual loading
with open("config.json") as f:
    data = json.load(f)
config = Config(**data)

# New way
from dataclassy import dataclassy

@dataclassy
class Config:
    host: str
    port: int

# Automatic loading
config = Config.from_path("config.json")
```

### Pattern 2: API Response Handling

```python
# Old way
@dataclass
class User:
    id: int
    name: str
    email: str

response = api.get_user(123)
user = User(
    id=response["id"],
    name=response["name"],
    email=response["email"]
)

# New way
@dataclassy
class User:
    id: int
    name: str
    email: str

response = api.get_user(123)
user = User.from_dict(response)
```

### Pattern 3: Validation

```python
# Old way
@dataclass
class Settings:
    color: str
    path: str
    
    def __post_init__(self):
        if not self.color.startswith("#"):
            raise ValueError("Invalid color")
        if not os.path.exists(self.path):
            raise ValueError("Path does not exist")

# New way
from dataclassy import dataclassy, Color, Path

@dataclassy
class Settings:
    color: Color  # Validates automatically
    path: Path = Path(must_exist=True)  # Validates automatically
```

## Compatibility Notes

### What Works Unchanged

- All dataclass parameters (`frozen`, `eq`, `order`, etc.)
- Field definitions with `field()`
- Default values and `default_factory`
- `__post_init__` method
- Inheritance
- `InitVar` fields
- All dataclasses functions (`fields()`, `asdict()`, `astuple()`, etc.)

### What's Enhanced

- `__post_init__` is enhanced to handle type conversions
- Enum fields get automatic string conversion
- New methods added (`from_dict`, `to_dict`, etc.)

### Edge Cases

1. **Custom `__new__`**: If you override `__new__`, ensure it's compatible with dataclassy's enhancements

2. **Slots**: Works with `slots=True`, but some dynamic features may be limited

3. **Metaclasses**: Custom metaclasses should be compatible, but test thoroughly

## Step-by-Step Migration Checklist

1. ✅ Change imports from `dataclasses` to `dataclassy`
2. ✅ Change decorator from `@dataclass` to `@dataclassy`
3. ✅ Run existing tests - they should all pass
4. ✅ Optionally adopt new features:
   - Replace manual dict conversion with `from_dict`
   - Replace manual file I/O with `from_path`/`to_path`
   - Add validation with field types
   - Use `@settings` for configuration classes
5. ✅ Update documentation to mention dataclassy features

## Getting Help

If you encounter any issues during migration:

1. Check that you're using Python 3.9+
2. Ensure all imports are updated
3. Look for custom `__new__` or `__init__` overrides
4. File an issue on GitHub with a minimal example

Remember: dataclassy is designed to be 100% backward compatible. If your existing dataclass code doesn't work with dataclassy, that's a bug!