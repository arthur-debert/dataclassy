"""Type-aware conversion between dictionaries and dataclasses."""

from dataclasses import fields, is_dataclass, MISSING
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_type_hints, get_origin, get_args

from ..utils import enum_converter

T = TypeVar("T")


class Converter:
    """Handles conversion between dictionaries and dataclass instances."""
    
    @staticmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Convert a dictionary to a dataclass instance with type awareness.
        
        Handles:
        - Nested dataclasses
        - Enum conversion (by value or name)
        - Optional[T] types
        - List[T] with dataclass elements
        - Dict[K, V] with dataclass values
        - Missing fields with defaults
        
        Args:
            cls: The dataclass type to convert to
            data: Dictionary containing the data
            
        Returns:
            Instance of the dataclass
            
        Raises:
            TypeError: If cls is not a dataclass
            ValueError: If required fields are missing
        """
        if not is_dataclass(cls):
            if data is None:
                return None
            return data
        
        if data is None:
            return None
        
        # Get type hints for better type information
        type_hints = get_type_hints(cls)
        init_kwargs = {}
        
        # Process each field
        for field in fields(cls):
            field_name = field.name
            field_value = data.get(field_name, MISSING)
            
            # Handle missing fields
            if field_value is MISSING:
                if field.default is not MISSING:
                    init_kwargs[field_name] = field.default
                elif field.default_factory is not MISSING:
                    init_kwargs[field_name] = field.default_factory()
                elif field.default is MISSING and field.default_factory is MISSING:
                    # Field is required but missing
                    raise ValueError(f"Missing required field: {field_name}")
                continue
            
            # Get the field type from type hints
            field_type = type_hints.get(field_name, field.type)
            
            # Handle None values
            if field_value is None:
                init_kwargs[field_name] = None
                continue
            
            # Convert the value based on its type
            converted_value = Converter._convert_value(field_value, field_type)
            init_kwargs[field_name] = converted_value
        
        return cls(**init_kwargs)
    
    @staticmethod
    def _convert_value(value: Any, target_type: Type) -> Any:
        """
        Convert a single value to the target type.
        
        Args:
            value: The value to convert
            target_type: The type to convert to
            
        Returns:
            The converted value
        """
        # Handle None
        if value is None:
            return None
        
        # Get origin for generic types
        origin = get_origin(target_type)
        
        # Handle Union types (including Optional)
        if origin is Union:
            args = get_args(target_type)
            # Filter out NoneType
            non_none_args = [arg for arg in args if arg is not type(None)]
            
            # If this is Optional[T] (Union[T, None])
            if len(non_none_args) == 1:
                return Converter._convert_value(value, non_none_args[0])
            else:
                # Try each type in the union
                for arg_type in non_none_args:
                    try:
                        return Converter._convert_value(value, arg_type)
                    except (ValueError, TypeError):
                        continue
                # If no conversion worked, return as-is
                return value
        
        # Handle List[T]
        elif origin is list:
            if not isinstance(value, list):
                return value
            
            args = get_args(target_type)
            if args:
                elem_type = args[0]
                return [Converter._convert_value(item, elem_type) for item in value]
            return value
        
        # Handle Dict[K, V]
        elif origin is dict:
            if not isinstance(value, dict):
                return value
            
            args = get_args(target_type)
            if len(args) >= 2:
                key_type, val_type = args[0], args[1]
                return {
                    Converter._convert_value(k, key_type): Converter._convert_value(v, val_type)
                    for k, v in value.items()
                }
            return value
        
        # Handle Enum types
        elif isinstance(target_type, type) and issubclass(target_type, Enum):
            if isinstance(value, target_type):
                return value
            try:
                converter = enum_converter(target_type)
                return converter(value)
            except ValueError:
                return value
        
        # Handle nested dataclasses
        elif is_dataclass(target_type):
            if isinstance(value, dict):
                return Converter.from_dict(target_type, value)
            return value
        
        # Handle basic type conversion
        elif isinstance(target_type, type):
            # If value is already the correct type, return it
            if isinstance(value, target_type):
                return value
            
            # Try to convert basic types
            try:
                if target_type in (int, float, str, bool):
                    return target_type(value)
            except (ValueError, TypeError):
                pass
        
        # Return value as-is if no conversion applied
        return value