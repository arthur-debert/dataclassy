"""Core dataclassy decorator implementation."""

from dataclasses import dataclass, fields, asdict, is_dataclass
from enum import Enum
from functools import wraps
from typing import Any, Optional, Type, TypeVar, Union, get_type_hints

from .utils import enum_converter

T = TypeVar("T")


def dataclassy(
    cls: Optional[Type[T]] = None,
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    match_args: bool = True,
    kw_only: bool = False,
    slots: bool = False,
) -> Union[Type[T], callable]:
    """
    Enhanced dataclass decorator that adds:
    - Automatic enum string conversion
    - from_dict/to_dict methods
    - from_path/to_path methods
    - Smart type conversion in __post_init__
    
    All parameters are passed through to the standard dataclass decorator,
    maintaining 100% compatibility.
    """
    def wrapper(cls: Type[T]) -> Type[T]:
        # Store original __post_init__ if exists BEFORE applying dataclass
        original_post_init = getattr(cls, "__post_init__", None)
        
        def enhanced_post_init(self) -> None:
            """Enhanced post-init that handles type conversions."""
            # Get type hints for the class
            type_hints = get_type_hints(self.__class__)
            
            # Run field conversions
            for field in fields(self):
                value = getattr(self, field.name)
                
                # Skip None values
                if value is None:
                    continue
                
                # Get the actual type from type hints
                field_type = type_hints.get(field.name, field.type)
                
                # Check if field type is an Enum
                if isinstance(field_type, type) and issubclass(field_type, Enum):
                    if not isinstance(value, field_type):
                        try:
                            converter = enum_converter(field_type)
                            converted = converter(value)
                            if frozen:
                                # Use object.__setattr__ for frozen instances
                                object.__setattr__(self, field.name, converted)
                            else:
                                setattr(self, field.name, converted)
                        except ValueError as e:
                            # Let the original value through if conversion fails
                            pass
            
            # Call original __post_init__ if exists
            if original_post_init:
                original_post_init(self)
        
        # Set __post_init__ BEFORE applying dataclass decorator
        if not slots:
            cls.__post_init__ = enhanced_post_init
        
        # Apply standard dataclass decorator
        cls = dataclass(
            cls,
            init=init,
            repr=repr,
            eq=eq,
            order=order,
            unsafe_hash=unsafe_hash,
            frozen=frozen,
            match_args=match_args,
            kw_only=kw_only,
            slots=slots,
        )
        
        # Add serialization methods
        @classmethod
        def from_dict(cls: Type[T], data: dict) -> T:
            """Create instance from dictionary."""
            # Import here to avoid circular imports
            from .serialization.converter import Converter
            return Converter.from_dict(cls, data)
        
        def to_dict(self) -> dict:
            """Convert instance to dictionary."""
            return asdict(self)
        
        @classmethod  
        def from_path(cls: Type[T], path: Union[str, Any]) -> T:
            """Load instance from file path."""
            # Import here to avoid circular imports
            from .serialization.formats import FormatHandler
            return FormatHandler.from_path(cls, path)
        
        def to_path(self, path: Union[str, Any]) -> None:
            """Save instance to file path."""
            # Import here to avoid circular imports
            from .serialization.formats import FormatHandler
            FormatHandler.to_path(self, path)
        
        # Add methods to class
        cls.from_dict = from_dict
        cls.to_dict = to_dict
        cls.from_path = from_path
        cls.to_path = to_path
        
        return cls
    
    # Handle being called with or without parentheses
    if cls is None:
        return wrapper
    else:
        return wrapper(cls)