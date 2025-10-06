"""Utility functions for dataclassy."""

from dataclasses import MISSING
from enum import Enum
from typing import Any, Type, TypeVar

T = TypeVar("T", bound=Enum)


def enum_converter(enum_class: Type[T]) -> callable:
    """
    Create a flexible enum converter that supports value and name matching.

    Args:
        enum_class: The Enum class to convert to

    Returns:
        A converter function that accepts various input formats
    """

    def convert(value: Any) -> T:
        if isinstance(value, enum_class):
            return value

        # Try by value
        try:
            return enum_class(value)
        except ValueError:
            pass

        # Try by name (case-insensitive)
        if isinstance(value, str):
            for member in enum_class:
                if member.name.lower() == value.lower():
                    return member

        raise ValueError(f"Cannot convert '{value}' to {enum_class.__name__}")

    return convert


def merge_configs(base: dict, override: dict, strategy: str = "deep") -> dict:
    """
    Merge two configuration dictionaries.

    Args:
        base: The base configuration
        override: The configuration to override with
        strategy: 'deep' for recursive merge, 'shallow' for top-level only

    Returns:
        Merged configuration dictionary
    """
    if strategy == "shallow":
        return {**base, **override}

    result = base.copy()

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge_configs(result[key], value, strategy)
        else:
            result[key] = value

    return result


def is_missing(value: Any) -> bool:
    """Check if a value is the dataclasses MISSING sentinel."""
    return value is MISSING
