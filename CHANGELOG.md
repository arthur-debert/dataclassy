# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of dataclassy
- Core `@dataclassy` decorator with 100% dataclass compatibility
- Enhanced `from_dict` method with nested dataclass support
- Smart enum conversion (by value or name, case-insensitive)
- Type-aware serialization handling Optional, List, and Dict types
- Built-in field validators:
  - `Color` field supporting hex strings, RGB tuples, and color names
  - `Path` field with validation, auto-loading, and helper methods
- File I/O support for JSON, YAML, TOML, and INI formats
- `@settings` decorator for configuration management:
  - Config file cascading with deep merge
  - Environment variable loading with prefix support
  - Docstring comment extraction for config files
  - Auto-discovery of config files by name
- Comprehensive test suite with 147 tests
- Full API documentation

### Changed
- Improved error handling with informative error messages
- Enhanced bool conversion to handle string values properly
- Path field parse_callback improvements

### Fixed
- Bool conversion from strings ("true"/"false")
- Silent error handling replaced with explicit exceptions
- Path field descriptor compatibility with dataclasses

## [0.1.0] - TBD

Initial release planned with core functionality.