"""Settings decorator for configuration management."""

import os
from dataclasses import fields, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_type_hints
from functools import wraps

from .core import dataclassy
from .serialization.formats import FormatHandler
from .utils import merge_configs

T = TypeVar("T")


def settings(
    cls: Optional[Type[T]] = None,
    *,
    # File loading options
    config_paths: Optional[List[Union[str, Path]]] = None,
    config_name: Optional[str] = None,
    search_dirs: Optional[List[Union[str, Path]]] = None,
    
    # Environment variable options
    env_prefix: Optional[str] = None,
    env_nested_delimiter: str = "__",
    
    # Merge options
    merge_strategy: str = "deep",
    
    # Other options
    auto_load: bool = True,
    case_sensitive: bool = False,
) -> Union[Type[T], callable]:
    """
    Enhanced dataclass decorator for configuration management.
    
    Adds the following features to a dataclass:
    - Automatic loading from config files (with cascading)
    - Environment variable override support
    - Deep merging of configurations
    - Comment generation from docstrings
    
    Args:
        cls: The class to decorate (used when called without parentheses)
        config_paths: Explicit paths to config files to load
        config_name: Base name for config files (e.g., "config" for config.json)
        search_dirs: Directories to search for config files
        env_prefix: Prefix for environment variables (e.g., "MYAPP_")
        env_nested_delimiter: Delimiter for nested env vars (e.g., "__" for MYAPP__DB__HOST)
        merge_strategy: How to merge configs ("deep" or "shallow")
        auto_load: Whether to automatically load config on class creation
        case_sensitive: Whether env var names are case-sensitive
        
    Example:
        @settings(env_prefix="MYAPP_", config_name="config")
        class AppConfig:
            '''Application configuration.'''
            debug: bool = False
            database_url: str = "sqlite:///app.db"
            port: int = 8000
            
        # Will automatically load from:
        # 1. config.json/yaml/toml in current dir
        # 2. Environment variables MYAPP_DEBUG, MYAPP_DATABASE_URL, MYAPP_PORT
    """
    def wrapper(cls: Type[T]) -> Type[T]:
        # First apply dataclassy decorator
        cls = dataclassy(cls)
        
        # Store settings metadata
        cls._settings_config = {
            "config_paths": config_paths or [],
            "config_name": config_name,
            "search_dirs": search_dirs or [Path.cwd()],
            "env_prefix": env_prefix,
            "env_nested_delimiter": env_nested_delimiter,
            "merge_strategy": merge_strategy,
            "case_sensitive": case_sensitive,
        }
        
        # Add load_config method
        @classmethod
        def load_config(
            cls: Type[T],
            config_paths: Optional[List[Union[str, Path]]] = None,
            load_env: bool = True,
            **overrides
        ) -> T:
            """
            Load configuration from files and environment variables.
            
            Args:
                config_paths: Additional config files to load
                load_env: Whether to load from environment variables
                **overrides: Keyword arguments to override loaded values
                
            Returns:
                Instance of the settings class with loaded configuration
            """
            # Start with empty config
            config = {}
            
            # Get paths to load
            paths = list(cls._settings_config["config_paths"])
            
            # Add provided paths
            if config_paths:
                paths.extend(config_paths)
            
            # Search for config files if config_name is provided
            if cls._settings_config["config_name"] and not paths:
                for search_dir in cls._settings_config["search_dirs"]:
                    search_dir = Path(search_dir)
                    for ext in ['.json', '.yaml', '.yml', '.toml', '.ini']:
                        path = search_dir / f"{cls._settings_config['config_name']}{ext}"
                        if path.exists():
                            paths.append(path)
            
            # Load and merge config files
            for path in paths:
                try:
                    # Load raw data instead of creating instances
                    # This prevents defaults from being filled in prematurely
                    path_obj = Path(path)
                    ext = path_obj.suffix.lower()
                    
                    if ext == '.json':
                        import json
                        with open(path_obj, 'r') as f:
                            loaded_dict = json.load(f)
                    elif ext in ['.yaml', '.yml']:
                        import yaml
                        with open(path_obj, 'r') as f:
                            loaded_dict = yaml.safe_load(f)
                    elif ext == '.toml':
                        try:
                            import tomllib
                        except ImportError:
                            import tomli as tomllib
                        with open(path_obj, 'rb') as f:
                            loaded_dict = tomllib.load(f)
                    elif ext == '.ini':
                        import configparser
                        parser = configparser.ConfigParser()
                        parser.read(path_obj)
                        loaded_dict = {}
                        sections = parser.sections()
                        if sections:
                            if parser.defaults():
                                loaded_dict.update(dict(parser.defaults()))
                            for section in sections:
                                loaded_dict[section] = dict(parser.items(section))
                        else:
                            if parser.defaults():
                                loaded_dict = dict(parser.defaults())
                    else:
                        # Unknown format, skip
                        continue
                    
                    config = merge_configs(
                        config,
                        loaded_dict,
                        cls._settings_config["merge_strategy"]
                    )
                except Exception:
                    # Ignore files that can't be loaded
                    pass
            
            # Load from environment variables
            if load_env and cls._settings_config["env_prefix"]:
                env_config = _load_from_env(
                    cls,
                    cls._settings_config["env_prefix"],
                    cls._settings_config["env_nested_delimiter"],
                    cls._settings_config["case_sensitive"]
                )
                config = merge_configs(
                    config,
                    env_config,
                    cls._settings_config["merge_strategy"]
                )
            
            # Apply overrides
            if overrides:
                config = merge_configs(
                    config,
                    overrides,
                    cls._settings_config["merge_strategy"]
                )
            
            # Create instance
            return cls.from_dict(config)
        
        # Add reload method
        def reload(self) -> None:
            """Reload configuration from sources."""
            new_config = self.__class__.load_config()
            # Update instance attributes
            for field in fields(self):
                setattr(self, field.name, getattr(new_config, field.name))
        
        # Add save_config method
        def save_config(
            self,
            path: Union[str, Path],
            include_defaults: bool = True,
            include_comments: bool = True,
            **kwargs
        ) -> None:
            """
            Save configuration to a file.
            
            Args:
                path: Path to save configuration to
                include_defaults: Whether to include fields with default values
                include_comments: Whether to include comments from docstrings
                **kwargs: Additional arguments for the file format
            """
            # Get data to save
            if include_defaults:
                data = asdict(self)
            else:
                data = {}
                from dataclasses import MISSING
                
                for field in fields(self):
                    value = getattr(self, field.name)
                    
                    # Check if field has a default value
                    if field.default is not MISSING:
                        # Has a simple default value - only save if changed
                        if value != field.default:
                            data[field.name] = value
                    elif field.default_factory is not MISSING:
                        # Has a default_factory - can't compare easily
                        # Try to call it and compare
                        try:
                            default_val = field.default_factory()
                            if value != default_val:
                                data[field.name] = value
                        except:
                            # If we can't create default, include the value
                            data[field.name] = value
                    else:
                        # No default - this is a required field, always include
                        data[field.name] = value
            
            # Handle saving based on whether we're including all fields or not
            if include_defaults:
                # Use FormatHandler with full object
                if include_comments:
                    # Add comments and save directly for JSON
                    save_data = data.copy()
                    save_data = _add_comments(self.__class__, save_data)
                    
                    path_obj = Path(path)
                    ext = path_obj.suffix.lower()
                    
                    if ext == '.json':
                        import json
                        with open(path_obj, 'w') as f:
                            json.dump(save_data, f, indent=kwargs.get('indent', 2))
                    else:
                        # For other formats, use FormatHandler without comments
                        FormatHandler.to_path(self, path, **kwargs)
                else:
                    FormatHandler.to_path(self, path, **kwargs)
            else:
                # We have a reduced data set - save it directly
                save_data = data.copy()
                
                if include_comments:
                    save_data = _add_comments(self.__class__, save_data)
                
                # Write directly based on format
                path_obj = Path(path)
                ext = path_obj.suffix.lower()
                
                if ext == '.json':
                    import json
                    with open(path_obj, 'w') as f:
                        json.dump(save_data, f, indent=kwargs.get('indent', 2))
                elif ext == '.yaml' or ext == '.yml':
                    try:
                        import yaml
                        with open(path_obj, 'w') as f:
                            yaml.dump(save_data, f)
                    except ImportError:
                        raise ImportError("PyYAML required for YAML support")
                else:
                    # For other formats, we need a full object
                    # Create temp object and use FormatHandler
                    temp_obj = self.__class__(**data)
                    FormatHandler.to_path(temp_obj, path, **kwargs)
        
        # Add methods to class
        cls.load_config = load_config
        cls.reload = reload
        cls.save_config = save_config
        
        # Auto-load if requested
        if auto_load:
            # Store the original __init__
            original_init = cls.__init__
            
            @wraps(original_init)
            def __init__(self, *args, **kwargs):
                # If called with no arguments, load from config
                if not args and not kwargs:
                    # Load config and get its data
                    loaded = cls.load_config()
                    loaded_data = asdict(loaded)
                    # Initialize with loaded data
                    original_init(self, **loaded_data)
                else:
                    # Normal instantiation
                    original_init(self, *args, **kwargs)
            
            cls.__init__ = __init__
        
        return cls
    
    # Handle being called with or without parentheses
    if cls is None:
        return wrapper
    else:
        return wrapper(cls)


def _load_from_env(
    cls: Type,
    prefix: str,
    delimiter: str,
    case_sensitive: bool
) -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Args:
        cls: The settings class
        prefix: Environment variable prefix
        delimiter: Delimiter for nested fields
        case_sensitive: Whether variable names are case-sensitive
        
    Returns:
        Dictionary of loaded values
    """
    config = {}
    type_hints = get_type_hints(cls)
    
    # Build mapping of env var names to field names
    env_map = {}
    for field in fields(cls):
        if case_sensitive:
            env_name = prefix + field.name.upper()
        else:
            env_name = prefix + field.name.upper()
        env_map[env_name] = field.name
    
    # Check environment variables
    for env_name, env_value in os.environ.items():
        if not case_sensitive:
            env_name = env_name.upper()
        
        # Check if this env var is for our config
        if env_name in env_map:
            field_name = env_map[env_name]
            field_type = type_hints.get(field_name, str)
            
            # Convert the string value to the appropriate type
            try:
                if field_type == bool:
                    # Special handling for booleans
                    value = env_value.lower() in ('true', '1', 'yes', 'on')
                elif field_type == int:
                    value = int(env_value)
                elif field_type == float:
                    value = float(env_value)
                else:
                    value = env_value
                    
                config[field_name] = value
            except (ValueError, TypeError):
                # Skip values that can't be converted
                pass
    
    return config


def _add_comments(cls: Type, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add comments from docstrings to the data.
    
    For JSON, adds _comment fields.
    For other formats, this is handled by format-specific writers.
    
    Args:
        cls: The settings class
        data: The configuration data
        
    Returns:
        Data with comments added
    """
    # Extract class docstring
    if cls.__doc__:
        lines = cls.__doc__.strip().split('\n')
        class_doc = []
        field_docs = {}
        current_field = None
        
        # Parse docstring to extract field documentation
        for line in lines:
            line = line.strip()
            
            # Check if this is a field documentation (field_name : type)
            if ' : ' in line and not line.startswith(' '):
                parts = line.split(' : ', 1)
                field_name = parts[0].strip()
                # Check if this field exists in the class
                if hasattr(cls, field_name):
                    current_field = field_name
                    field_docs[field_name] = []
                else:
                    current_field = None
                    class_doc.append(line)
            elif current_field and line:
                # This is documentation for the current field
                field_docs[current_field].append(line)
            elif not current_field:
                # This is part of the class documentation
                class_doc.append(line)
        
        # Add class comment
        if class_doc:
            data["_comment"] = '\n'.join(class_doc).strip()
        
        # Add field comments
        for field_name, doc_lines in field_docs.items():
            if field_name in data and doc_lines:
                comment_key = f"_{field_name}_comment"
                data[comment_key] = ' '.join(doc_lines).strip()
    
    return data