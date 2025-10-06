"""Base validator descriptor for custom field types."""

from typing import Any, Optional


class Validator:
    """
    Base validator using Python's descriptor protocol.
    
    Subclasses should override:
    - convert(value): Convert/normalize the value before validation
    - validate(value): Validate the converted value
    
    The descriptor protocol ensures validators work with:
    - Regular dataclasses
    - Frozen dataclasses
    - Inheritance
    """
    
    def __init__(self, **kwargs):
        """
        Initialize validator with optional keyword arguments.
        
        Args:
            **kwargs: Arguments specific to the validator subclass
        """
        self.kwargs = kwargs
        # These will be set by __set_name__
        self.private_name: Optional[str] = None
        self.public_name: Optional[str] = None
    
    def __set_name__(self, owner: type, name: str) -> None:
        """
        Called when the descriptor is assigned to a class attribute.
        
        Args:
            owner: The class that owns this descriptor
            name: The name of the attribute
        """
        self.private_name = '_' + name
        self.public_name = name
    
    def __get__(self, obj: Any, objtype: Optional[type] = None) -> Any:
        """
        Get the value of the attribute.
        
        Args:
            obj: The instance to get the value from
            objtype: The type of the instance
            
        Returns:
            The attribute value or self if accessed on the class
        """
        if obj is None:
            # Accessed on class, return descriptor itself
            return self
        return getattr(obj, self.private_name, None)
    
    def __set__(self, obj: Any, value: Any) -> None:
        """
        Set the value of the attribute with conversion and validation.
        
        Args:
            obj: The instance to set the value on
            value: The value to set
            
        Raises:
            ValueError: If validation fails
            TypeError: If type conversion fails
        """
        # Allow None values by default
        if value is None:
            setattr(obj, self.private_name, None)
            return
            
        # Convert the value
        converted_value = self.convert(value)
        
        # Validate the converted value
        self.validate(converted_value)
        
        # Store the validated value
        setattr(obj, self.private_name, converted_value)
    
    def convert(self, value: Any) -> Any:
        """
        Convert/normalize the value before validation.
        
        Override this method in subclasses to implement custom conversion.
        
        Args:
            value: The value to convert
            
        Returns:
            The converted value
        """
        return value
    
    def validate(self, value: Any) -> None:
        """
        Validate the converted value.
        
        Override this method in subclasses to implement custom validation.
        Should raise ValueError or TypeError if validation fails.
        
        Args:
            value: The value to validate
            
        Raises:
            ValueError: If the value is invalid
            TypeError: If the value is the wrong type
        """
        pass