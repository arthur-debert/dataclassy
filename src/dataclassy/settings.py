"""Settings decorator for configuration management."""

import os
from dataclasses import fields, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Tuple, get_type_hints, get_origin, get_args
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
                    # Save with format-aware comments
                    _save_with_format_aware_comments(
                        self.__class__, data, path, include_comments, **kwargs
                    )
                else:
                    FormatHandler.to_path(self, path, **kwargs)
            else:
                # We have a reduced data set - save it directly
                _save_with_format_aware_comments(
                    self.__class__, data, path, include_comments, **kwargs
                )
        
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
                value = _convert_env_value(env_value, field_type)
                config[field_name] = value
            except (ValueError, TypeError):
                # Skip values that can't be converted
                pass
    
    return config


def _convert_env_value(value: str, target_type: Type) -> Any:
    """
    Convert environment variable string to target type.
    
    Handles:
    - Basic types (bool, int, float, str)
    - List types (comma-separated)
    - Dict types (key=value pairs)
    - Optional types
    """
    from typing import get_origin, get_args
    
    # Get origin for generic types
    origin = get_origin(target_type)
    
    # Handle Optional types
    if origin is Union:
        args = get_args(target_type)
        # Check if it's explicitly None/null
        if value.lower() in ('none', 'null'):
            return None
        # Try each type in the union
        for arg_type in args:
            if arg_type is type(None):
                continue
            try:
                return _convert_env_value(value, arg_type)
            except:
                continue
        return value
    
    # Handle List types
    if origin is list or target_type is list:
        if not value.strip():
            return []
        
        # Split by comma, strip whitespace
        items = [item.strip() for item in value.split(',')]
        
        # If we have type args, convert each item
        if origin is list:
            args = get_args(target_type)
            if args:
                item_type = args[0]
                items = [_convert_env_value(item, item_type) for item in items]
        
        return items
    
    # Handle Dict types
    if origin is dict or target_type is dict:
        if not value.strip():
            return {}
        
        result = {}
        # Support both JSON and key=value format
        if value.startswith('{'):
            # Try JSON format
            try:
                import json
                return json.loads(value)
            except:
                pass
        
        # Parse key=value pairs
        for pair in value.split(','):
            if '=' in pair:
                k, v = pair.split('=', 1)
                k = k.strip()
                v = v.strip()
                
                # If we have type args, convert the value
                if origin is dict:
                    args = get_args(target_type)
                    if len(args) >= 2:
                        key_type, val_type = args[0], args[1]
                        k = _convert_env_value(k, key_type) if key_type != str else k
                        v = _convert_env_value(v, val_type)
                
                result[k] = v
        
        return result
    
    # Handle None/null for basic types
    if value.lower() in ('none', 'null', ''):
        return None
    
    # Handle basic types
    if target_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    elif target_type == int:
        return int(value)
    elif target_type == float:
        return float(value)
    elif target_type == str:
        return value
    else:
        # For other types, try to call the type directly
        try:
            return target_type(value)
        except:
            return value


def _extract_docstring_comments(cls: Type) -> Tuple[str, Dict[str, str]]:
    """
    Extract class and field documentation from docstrings.
    
    Args:
        cls: The settings class
        
    Returns:
        Tuple of (class_doc, field_docs)
    """
    class_doc = ""
    field_docs = {}
    
    if cls.__doc__:
        lines = cls.__doc__.strip().split('\n')
        class_lines = []
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
                    class_lines.append(line)
            elif current_field and line:
                # This is documentation for the current field
                field_docs[current_field].append(line)
            elif not current_field:
                # This is part of the class documentation
                class_lines.append(line)
        
        # Join class documentation
        if class_lines:
            class_doc = '\n'.join(class_lines).strip()
        
        # Join field documentation
        for field_name, doc_lines in field_docs.items():
            if doc_lines:
                field_docs[field_name] = ' '.join(doc_lines).strip()
    
    return class_doc, field_docs


def _add_comments(cls: Type, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add comments from docstrings to the data (JSON format).
    
    This is kept for backward compatibility and JSON-specific handling.
    """
    class_doc, field_docs = _extract_docstring_comments(cls)
    
    if class_doc:
        data["_comment"] = class_doc
    
    for field_name, doc in field_docs.items():
        if field_name in data and doc:
            data[f"_{field_name}_comment"] = doc
    
    return data


def _save_with_format_aware_comments(
    cls: Type,
    data: Dict[str, Any],
    path: Union[str, Path],
    include_comments: bool,
    **kwargs
) -> None:
    """
    Save data with format-appropriate comment handling.
    
    Args:
        cls: The class with docstrings
        data: Data to save
        path: File path
        include_comments: Whether to include comments
        **kwargs: Additional format-specific options
    """
    path_obj = Path(path)
    ext = path_obj.suffix.lower()
    
    if not include_comments:
        # No comments - use appropriate format handler
        if ext == '.json':
            import json
            with open(path_obj, 'w') as f:
                json.dump(data, f, indent=kwargs.get('indent', 2))
        elif ext in ['.yaml', '.yml']:
            try:
                import yaml
                with open(path_obj, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False,
                            sort_keys=kwargs.get('sort_keys', False))
            except ImportError:
                raise ImportError("PyYAML required for YAML support")
        elif ext == '.toml':
            try:
                import tomli_w
                with open(path_obj, 'wb') as f:
                    tomli_w.dump(data, f)
            except ImportError:
                raise ImportError("tomli-w required for TOML support")
        elif ext == '.ini':
            # For INI, we need special handling
            import configparser
            parser = configparser.ConfigParser()
            for key, value in data.items():
                parser.set('DEFAULT', key, str(value))
            with open(path_obj, 'w') as f:
                parser.write(f)
        else:
            raise ValueError(f"Unsupported format: {ext}")
        return
    
    # Extract comments
    class_doc, field_docs = _extract_docstring_comments(cls)
    
    if ext == '.json':
        # For JSON, add comment fields to data
        save_data = data.copy()
        if class_doc:
            save_data["_comment"] = class_doc
        for field_name, doc in field_docs.items():
            if field_name in save_data and doc:
                save_data[f"_{field_name}_comment"] = doc
        
        import json
        with open(path_obj, 'w') as f:
            json.dump(save_data, f, indent=kwargs.get('indent', 2))
    
    elif ext in ['.yaml', '.yml']:
        # For YAML, try to use ruamel.yaml for native comments
        try:
            from ruamel.yaml import YAML
            from ruamel.yaml.comments import CommentedMap
            
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False
            yaml.width = 4096
            
            # Create commented map
            yaml_data = CommentedMap(data)
            
            # Add comments
            if class_doc:
                # Add as document-level comment
                yaml_data.yaml_set_start_comment(class_doc)
            
            # Add field comments
            for field_name, doc in field_docs.items():
                if field_name in yaml_data and doc:
                    yaml_data.yaml_set_comment_before_after_key(
                        field_name, before=doc, indent=0
                    )
            
            with open(path_obj, 'w') as f:
                yaml.dump(yaml_data, f)
                
        except ImportError:
            # Fallback to PyYAML with manual comment writing
            try:
                import yaml
                with open(path_obj, 'w') as f:
                    if class_doc:
                        # Write class comment at the top
                        for line in class_doc.split('\n'):
                            f.write(f"# {line}\n")
                        f.write("\n")
                    
                    # For field comments, we'd need to manually inject them
                    # which is complex with PyYAML, so just dump normally
                    yaml.dump(data, f, default_flow_style=False,
                            sort_keys=kwargs.get('sort_keys', False))
            except ImportError:
                raise ImportError("PyYAML or ruamel.yaml required for YAML support")
    
    elif ext == '.toml':
        # For TOML, try tomlkit for comment support
        try:
            import tomlkit
            
            doc = tomlkit.document()
            
            # Add class comment
            if class_doc:
                for line in class_doc.split('\n'):
                    doc.add(tomlkit.comment(line))
                doc.add(tomlkit.nl())
            
            # Add fields with comments
            for key, value in data.items():
                if key in field_docs and field_docs[key]:
                    # Add field comment
                    for line in field_docs[key].split('\n'):
                        doc.add(tomlkit.comment(line))
                doc.add(key, value)
            
            with open(path_obj, 'w') as f:
                f.write(tomlkit.dumps(doc))
                
        except ImportError:
            # Fallback to tomli-w without comments
            try:
                import tomli_w
                with open(path_obj, 'wb') as f:
                    tomli_w.dump(data, f)
            except ImportError:
                raise ImportError("tomlkit or tomli-w required for TOML support")
    
    elif ext == '.ini':
        # For INI, write comments as actual comments
        import configparser
        
        with open(path_obj, 'w') as f:
            if class_doc:
                for line in class_doc.split('\n'):
                    f.write(f"# {line}\n")
                f.write("\n")
            
            parser = configparser.ConfigParser()
            
            # Add fields
            for key, value in data.items():
                if key in field_docs and field_docs[key]:
                    # Can't add inline comments with configparser
                    # so we skip field comments for INI
                    pass
                parser.set('DEFAULT', key, str(value))
            
            parser.write(f)
    
    else:
        raise ValueError(f"Unsupported format: {ext}")