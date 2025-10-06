"""File format handlers for dataclassy serialization."""

import json
from pathlib import Path
from typing import Any, Union

from dataclasses import asdict

from .converter import Converter


class FormatHandler:
    """Handles loading and saving dataclasses to various file formats."""

    @staticmethod
    def from_path(cls: type, path: Union[str, Path]) -> Any:
        """
        Load a dataclass instance from a file.

        Automatically detects format based on file extension.
        Supported formats: .json, .yaml, .yml, .toml, .ini

        Args:
            cls: The dataclass type to load into
            path: Path to the file

        Returns:
            Instance of the dataclass

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
            ImportError: If required library for format is not installed
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Determine format from extension
        ext = path.suffix.lower()

        if ext == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

        elif ext in [".yaml", ".yml"]:
            try:
                import yaml
            except ImportError:
                raise ImportError(
                    "PyYAML is required for YAML support. "
                    "Install with: pip install dataclassy[yaml]"
                )
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

        elif ext == ".toml":
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib
                except ImportError:
                    raise ImportError(
                        "tomli is required for TOML support on Python < 3.11. "
                        "Install with: pip install dataclassy[toml]"
                    )
            with open(path, "rb") as f:
                data = tomllib.load(f)

        elif ext == ".ini":
            import configparser

            parser = configparser.ConfigParser()
            parser.read(path)

            # Convert INI to dict format
            data = {}

            # Check if there are any sections
            sections = parser.sections()

            if sections:
                # Has sections - combine DEFAULT and section data
                data = {}

                # Start with defaults if any
                if parser.defaults():
                    data.update(dict(parser.defaults()))

                # Add section data
                for section in sections:
                    data[section] = dict(parser.items(section))
            else:
                # No sections, only DEFAULT section
                if parser.defaults():
                    data = dict(parser.defaults())
                else:
                    data = {}

        else:
            raise ValueError(
                f"Unsupported file format: {ext}. "
                f"Supported formats: .json, .yaml, .yml, .toml, .ini"
            )

        return Converter.from_dict(cls, data)

    @staticmethod
    def to_path(obj: Any, path: Union[str, Path], **kwargs) -> None:
        """
        Save a dataclass instance to a file.

        Automatically detects format based on file extension.
        Supported formats: .json, .yaml, .yml, .toml, .ini

        Args:
            obj: The dataclass instance to save
            path: Path to save to
            **kwargs: Additional arguments passed to the serializer
                - indent: For JSON, indentation level (default: 2)
                - default_flow_style: For YAML (default: False)
                - sort_keys: For JSON/YAML (default: False)

        Raises:
            ValueError: If the file format is not supported
            ImportError: If required library for format is not installed
        """
        path = Path(path)

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        data = asdict(obj)

        # Determine format from extension
        ext = path.suffix.lower()

        if ext == ".json":
            indent = kwargs.get("indent", 2)
            sort_keys = kwargs.get("sort_keys", False)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, sort_keys=sort_keys)

        elif ext in [".yaml", ".yml"]:
            try:
                import yaml
            except ImportError:
                raise ImportError(
                    "PyYAML is required for YAML support. "
                    "Install with: pip install dataclassy[yaml]"
                )

            default_flow_style = kwargs.get("default_flow_style", False)
            sort_keys = kwargs.get("sort_keys", False)

            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=default_flow_style,
                    sort_keys=sort_keys,
                )

        elif ext == ".toml":
            try:
                import tomllib
                import tomli_w
            except ImportError:
                try:
                    import tomli as tomllib
                    import tomli_w
                except ImportError:
                    raise ImportError(
                        "tomli-w is required for TOML writing. "
                        "Install with: pip install dataclassy[toml]"
                    )

            with open(path, "wb") as f:
                tomli_w.dump(data, f)

        elif ext == ".ini":
            import configparser

            parser = configparser.ConfigParser()

            # Check if there are any dict values that should become sections
            dict_fields = {k: v for k, v in data.items() if isinstance(v, dict)}

            if dict_fields:
                # Multi-section INI - dict fields become sections
                for section, values in dict_fields.items():
                    parser.add_section(section)
                    for key, value in values.items():
                        parser.set(section, key, str(value))

                # Non-dict fields go to DEFAULT section
                non_dict_fields = {
                    k: v for k, v in data.items() if not isinstance(v, dict)
                }
                for key, value in non_dict_fields.items():
                    parser.set("DEFAULT", key, str(value))
            else:
                # Single section INI - all fields to DEFAULT
                for key, value in data.items():
                    parser.set("DEFAULT", key, str(value))

            with open(path, "w", encoding="utf-8") as f:
                parser.write(f)

        else:
            raise ValueError(
                f"Unsupported file format: {ext}. "
                f"Supported formats: .json, .yaml, .yml, .toml, .ini"
            )
