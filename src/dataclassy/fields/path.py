"""Path field type for dataclassy."""

from pathlib import Path as PathLib
from typing import Any, Callable, List, Optional, Union

from .validators import Validator


class Path(Validator):
    """
    Field type for file system paths with validation and auto-loading.
    
    Features:
    - Automatic conversion to pathlib.Path
    - Existence validation
    - File type validation (file vs directory)
    - Extension validation
    - Optional auto-loading of file contents
    - Path resolution and normalization
    """
    
    def __init__(
        self,
        *,
        must_exist: bool = False,
        is_file: Optional[bool] = None,
        is_dir: Optional[bool] = None,
        extensions: Optional[List[str]] = None,
        resolve: bool = True,
        expanduser: bool = True,
        create_parents: bool = False,
        parse_callback: Optional[Callable[[PathLib], Any]] = None,
        parsed_attr: Optional[str] = None,
        raise_parse_errors: bool = False
    ):
        """
        Initialize Path validator.
        
        Args:
            must_exist: Whether the path must exist
            is_file: Whether the path must be a file (None = don't check)
            is_dir: Whether the path must be a directory (None = don't check)
            extensions: Allowed file extensions (e.g., ['.txt', '.md'])
            resolve: Whether to resolve the path to absolute
            expanduser: Whether to expand ~ to user home directory
            create_parents: Whether to create parent directories if they don't exist
            parse_callback: Optional callback to parse/load file contents
            parsed_attr: Name of attribute to store parsed data (default: field_name + '_data')
            raise_parse_errors: Whether to raise exceptions from parse_callback
        """
        super().__init__()
        self.must_exist = must_exist
        self.is_file = is_file
        self.is_dir = is_dir
        self.extensions = extensions
        self.resolve = resolve
        self.expanduser = expanduser
        self.create_parents = create_parents
        self.parse_callback = parse_callback
        self.parsed_attr = parsed_attr
        self.raise_parse_errors = raise_parse_errors
        
        # Validate parameters
        if is_file and is_dir:
            raise ValueError("Path cannot be both file and directory")
    
    def convert(self, value: Any) -> PathLib:
        """
        Convert value to pathlib.Path.
        
        Args:
            value: String path or Path object
            
        Returns:
            pathlib.Path object
        """
        if isinstance(value, PathLib):
            path = value
        elif isinstance(value, str):
            path = PathLib(value)
        else:
            # Let validation handle the error
            return value
        
        # Expand user directory
        if self.expanduser:
            path = path.expanduser()
        
        # Resolve to absolute path
        if self.resolve:
            try:
                path = path.resolve()
            except Exception:
                # If resolution fails, keep the original path
                pass
        
        # Create parent directories if requested
        if self.create_parents and not path.exists():
            try:
                if self.is_dir:
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                # Ignore errors during creation
                pass
        
        return path
    
    def validate(self, value: Any) -> None:
        """
        Validate the path.
        
        Args:
            value: The converted Path object
            
        Raises:
            TypeError: If value is not a Path
            ValueError: If path validation fails
        """
        if not isinstance(value, PathLib):
            raise TypeError(
                f"{self.public_name} must be a string or Path object, "
                f"got {type(value).__name__}"
            )
        
        # Check existence
        if self.must_exist and not value.exists():
            raise ValueError(f"{self.public_name} does not exist: {value}")
        
        # Skip further checks if path doesn't exist
        if not value.exists():
            return
        
        # Check file type
        if self.is_file is True and not value.is_file():
            raise ValueError(f"{self.public_name} must be a file: {value}")
        
        if self.is_dir is True and not value.is_dir():
            raise ValueError(f"{self.public_name} must be a directory: {value}")
        
        # Check extensions
        if self.extensions and value.is_file():
            if value.suffix not in self.extensions:
                raise ValueError(
                    f"{self.public_name} must have extension in {self.extensions}, "
                    f"got {value.suffix}"
                )
    
    def __set__(self, obj: Any, value: Any) -> None:
        """
        Set the path value with optional auto-loading.
        
        Args:
            obj: The instance to set the value on
            value: The path value
        """
        # Call parent to handle conversion and validation
        super().__set__(obj, value)
        
        # If parse_callback is provided, load and parse the file
        if self.parse_callback and value is not None:
            path = getattr(obj, self.private_name)
            if path and path.exists() and path.is_file():
                # Determine the attribute name for parsed data
                if self.parsed_attr:
                    parsed_attr = self.parsed_attr
                else:
                    # Default: use the public field name + '_data'
                    parsed_attr = self.public_name + '_data'
                
                try:
                    # Call the parse callback with the path
                    parsed_data = self.parse_callback(path)
                    # Store the parsed data
                    setattr(obj, parsed_attr, parsed_data)
                except Exception as e:
                    if self.raise_parse_errors:
                        raise ValueError(
                            f"Failed to parse {self.public_name}: {e}"
                        ) from e
                    else:
                        # Store None if parsing fails and we're not raising
                        setattr(obj, parsed_attr, None)
    
    def read_text(self, obj: Any, encoding: str = 'utf-8') -> Optional[str]:
        """
        Read the file contents as text.
        
        Args:
            obj: The instance containing this path field
            encoding: Text encoding
            
        Returns:
            File contents or None if file doesn't exist
        """
        path = self.__get__(obj)
        if path and path.exists() and path.is_file():
            try:
                return path.read_text(encoding=encoding)
            except Exception:
                return None
        return None
    
    def read_bytes(self, obj: Any) -> Optional[bytes]:
        """
        Read the file contents as bytes.
        
        Args:
            obj: The instance containing this path field
            
        Returns:
            File contents or None if file doesn't exist
        """
        path = self.__get__(obj)
        if path and path.exists() and path.is_file():
            try:
                return path.read_bytes()
            except Exception:
                return None
        return None
    
    def write_text(self, obj: Any, content: str, encoding: str = 'utf-8') -> bool:
        """
        Write text content to the file.
        
        Args:
            obj: The instance containing this path field
            content: Text content to write
            encoding: Text encoding
            
        Returns:
            True if successful, False otherwise
        """
        path = self.__get__(obj)
        if path:
            try:
                path.write_text(content, encoding=encoding)
                return True
            except Exception:
                return False
        return False