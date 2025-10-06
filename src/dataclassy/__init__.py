"""
Dataclassy: Enhanced dataclasses with validation, serialization, and configuration management.

100% compatible with Python's built-in dataclasses module.
"""

from dataclasses import field, fields, Field, MISSING, is_dataclass, asdict, astuple

from .core import dataclassy

__version__ = "0.0.1"

__all__ = [
    # Our additions
    "dataclassy",
    # Re-exported from dataclasses for convenience
    "field",
    "fields", 
    "Field",
    "MISSING",
    "is_dataclass",
    "asdict",
    "astuple",
]