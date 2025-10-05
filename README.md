# Dataclassy

## The project

A Python library for creating and managing data classes with enhanced
functionality. The core proposal is to be : 

- 100% compatible with Python's built-in `dataclasses` module.
- No extra learning curve for users familiar with `dataclasses`.
- Lightweight and easy to use, but does bring some functionality
- Field library for common field types and validation.
- Superset of `dataclasses` functionality, can be used anywhere a dataclass
  can..


Features: 
    - from dict handles nested dataclasses
    - Can be smart about enums in from dict.
    - include  from(path | or dict): can load from json , yaml, toml, ini and
      to(path | or dict): can dump to json , yaml, toml and ini
    - has @settings decorator for easy configuration management
        - smart merge (like user settings override default settings), nested.
        - can load from env vars
        - will use doc strings for commenting config files (for json, uses "_comment"
          fields)
     - can be seamless integrated with click (for choices, for example)


Fields: 

Color (accepts hex strings, rgb tuples, and color names)
Path (for file system paths, callback for parsing, will auto load for json
yaml, can restrict to path, 


## Resourses

The [docs](./docs.md) has a deep dive into python's dataclasses and how to
extend / change them


## Codebase Guidelines

- Testing
    - pytest, pure functions, no classes unless necessary
    - liberal use of pytest parametrize for multiple inputs.
-   - Use fixtures for common test data  
    - No integration tests, only unit tests.

