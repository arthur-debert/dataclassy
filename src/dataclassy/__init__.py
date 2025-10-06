"""
Dataclassy: Enhanced dataclasses with validation, serialization, and configuration management.

100% compatible with Python's built-in dataclasses module.
"""

from dataclasses import field, fields, Field, MISSING, is_dataclass, asdict, astuple

from .core import dataclassy
from .fields import Color, Path
from .settings import settings

__version__ = "0.1.0"

__all__ = [
    # Our additions
    "dataclassy",
    "settings",
    "Color",
    "Path",
    # Re-exported from dataclasses for convenience
    "field",
    "fields", 
    "Field",
    "MISSING",
    "is_dataclass",
    "asdict",
    "astuple",
]