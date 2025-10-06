"""Tests for dataclassy field types."""

import pytest
from pathlib import Path as PathLib
import tempfile
import os

from dataclassy import dataclassy, Color, Path


class TestColorField:
    """Tests for Color field type."""
    
    def test_hex_color_normalization(self):
        """Test hex color string normalization."""
        @dataclassy
        class Theme:
            primary: Color = Color()
            secondary: Color = Color()
        
        # Test with # prefix
        theme = Theme("#ff0000", "#00FF00")
        assert theme.primary == "#FF0000"
        assert theme.secondary == "#00FF00"
        
        # Test without # prefix
        theme2 = Theme("ff0000", "00ff00")
        assert theme2.primary == "#FF0000"
        assert theme2.secondary == "#00FF00"
        
        # Test 3-digit hex
        theme3 = Theme("#f00", "0f0")
        assert theme3.primary == "#FF0000"
        assert theme3.secondary == "#00FF00"
    
    def test_rgb_tuple_conversion(self):
        """Test RGB tuple to hex conversion."""
        @dataclassy
        class Palette:
            color: Color = Color()
        
        # Standard RGB
        p1 = Palette((255, 0, 0))
        assert p1.color == "#FF0000"
        
        p2 = Palette([0, 255, 0])  # List also works
        assert p2.color == "#00FF00"
        
        # Values get clamped to 0-255
        p3 = Palette((300, -50, 128))
        assert p3.color == "#FF0080"
        
        # Float values get converted to int
        p4 = Palette((127.5, 0.0, 255.9))
        assert p4.color == "#7F00FF"
    
    def test_named_colors(self):
        """Test named color conversion."""
        @dataclassy
        class Design:
            bg_color: Color = Color()
            fg_color: Color = Color()
        
        design = Design("red", "BLUE")  # Case insensitive
        assert design.bg_color == "#FF0000"
        assert design.fg_color == "#0000FF"
        
        # Test various named colors
        test_colors = {
            "black": "#000000",
            "white": "#FFFFFF",
            "navy": "#000080",
            "gray": "#808080",
            "grey": "#808080",  # Both spellings work
            "orange": "#FFA500",
            "purple": "#800080",
        }
        
        for name, expected in test_colors.items():
            d = Design(name, "black")
            assert d.bg_color == expected
    
    def test_invalid_colors(self):
        """Test invalid color values raise errors."""
        @dataclassy
        class BadColors:
            color: Color = Color()
        
        # Invalid hex string
        with pytest.raises(ValueError, match="must be a valid hex color"):
            BadColors("#GGGGGG")
        
        with pytest.raises(ValueError, match="must be a valid hex color"):
            BadColors("12345")  # Only 5 digits
        
        # Invalid type
        with pytest.raises(TypeError, match="must be a color string"):
            BadColors(12345)
        
        # Invalid RGB tuple
        with pytest.raises(TypeError):  # Wrong number of values returns tuple
            BadColors((255, 0))  # Only 2 values
        
        # Invalid color name
        with pytest.raises(ValueError):
            BadColors("notacolor")
    
    def test_color_helper_methods(self):
        """Test Color helper methods."""
        @dataclassy
        class Widget:
            color: Color = Color()
        
        widget = Widget("#FF8040")
        
        # Test to_rgb - access descriptor from class
        rgb = Widget.color.to_rgb(widget)
        assert rgb == (255, 128, 64)
        
        # Test to_css - access descriptor from class
        css = Widget.color.to_css(widget)
        assert css == "#ff8040"
        
        # Test with None value
        widget2 = Widget(None)  # Need to provide explicit None
        assert Widget.color.to_rgb(widget2) == (0, 0, 0)
        assert Widget.color.to_css(widget2) == "#000000"
    
    def test_color_with_dataclassy_features(self):
        """Test Color field works with dataclassy features."""
        @dataclassy
        class ColorScheme:
            name: str
            primary: Color = Color()
            secondary: Color = Color()
            accent: Color = Color()
        
        # Test from_dict
        data = {
            "name": "Ocean",
            "primary": "navy",
            "secondary": (64, 128, 255),
            "accent": "#00FFFF"
        }
        
        scheme = ColorScheme.from_dict(data)
        assert scheme.name == "Ocean"
        assert scheme.primary == "#000080"
        assert scheme.secondary == "#4080FF"
        assert scheme.accent == "#00FFFF"
        
        # Test to_dict
        result = scheme.to_dict()
        assert result["primary"] == "#000080"


class TestPathField:
    """Tests for Path field type."""
    
    def test_basic_path_conversion(self):
        """Test basic path string to Path conversion."""
        @dataclassy
        class FileConfig:
            input_file: Path = Path()
            output_dir: Path = Path()
        
        config = FileConfig("/tmp/input.txt", "/tmp/output")
        assert isinstance(config.input_file, PathLib)
        assert isinstance(config.output_dir, PathLib)
        # On macOS, /tmp resolves to /private/tmp
        assert str(config.input_file).endswith("tmp/input.txt")
    
    def test_path_expansion(self):
        """Test user directory expansion."""
        @dataclassy
        class UserPaths:
            home_file: Path = Path(expanduser=True)
            no_expand: Path = Path(expanduser=False, resolve=False)
        
        paths = UserPaths("~/test.txt", "~/test.txt")
        assert str(paths.home_file).startswith(str(PathLib.home()))
        assert str(paths.no_expand) == "~/test.txt"
    
    def test_path_validation(self):
        """Test path validation options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = PathLib(tmpdir) / "test.txt"
            test_file.write_text("content")
            
            @dataclassy
            class ValidatedPaths:
                must_exist: Path = Path(must_exist=True)
                optional: Path = Path(must_exist=False)
            
            # Valid paths
            vp = ValidatedPaths(str(test_file), "/nonexistent/path")
            assert vp.must_exist.exists()
            assert not vp.optional.exists()
            
            # Invalid path
            with pytest.raises(ValueError, match="does not exist"):
                ValidatedPaths("/nonexistent/required", "/whatever")
    
    def test_file_type_validation(self):
        """Test file vs directory validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file and directory
            test_file = PathLib(tmpdir) / "file.txt"
            test_file.write_text("content")
            test_dir = PathLib(tmpdir) / "subdir"
            test_dir.mkdir()
            
            @dataclassy
            class TypedPaths:
                file_path: Path = Path(is_file=True, must_exist=True)
                dir_path: Path = Path(is_dir=True, must_exist=True)
            
            # Correct types
            tp = TypedPaths(str(test_file), str(test_dir))
            assert tp.file_path.is_file()
            assert tp.dir_path.is_dir()
            
            # Wrong type - file where directory expected
            with pytest.raises(ValueError, match="must be a directory"):
                TypedPaths(str(test_file), str(test_file))
            
            # Wrong type - directory where file expected
            with pytest.raises(ValueError, match="must be a file"):
                TypedPaths(str(test_dir), str(test_dir))
    
    def test_extension_validation(self):
        """Test file extension validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = PathLib(tmpdir) / "doc.txt"
            txt_file.write_text("text")
            py_file = PathLib(tmpdir) / "script.py"
            py_file.write_text("code")
            
            @dataclassy
            class CodeFiles:
                source: Path = Path(extensions=['.py', '.pyx'], must_exist=True)
            
            # Valid extension
            cf = CodeFiles(str(py_file))
            assert cf.source.suffix == ".py"
            
            # Invalid extension
            with pytest.raises(ValueError, match="must have extension in"):
                CodeFiles(str(txt_file))
    
    def test_path_creation(self):
        """Test automatic parent directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            @dataclassy
            class OutputPaths:
                output_file: Path = Path(create_parents=True)
                output_dir: Path = Path(create_parents=True, is_dir=True)
            
            # Non-existent paths
            file_path = PathLib(tmpdir) / "new" / "sub" / "file.txt"
            dir_path = PathLib(tmpdir) / "new" / "dirs"
            
            op = OutputPaths(str(file_path), str(dir_path))
            
            # Parent directories should be created
            assert op.output_file.parent.exists()
            assert op.output_dir.exists()
            assert op.output_dir.is_dir()
    
    def test_path_helper_methods(self):
        """Test Path helper methods for reading/writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = PathLib(tmpdir) / "test.txt"
            test_file.write_text("Hello World")
            
            @dataclassy
            class FileHandler:
                path: Path = Path()
            
            handler = FileHandler(str(test_file))
            
            # Test read_text - access descriptor from class
            content = FileHandler.path.read_text(handler)
            assert content == "Hello World"
            
            # Test write_text - access descriptor from class
            success = FileHandler.path.write_text(handler, "New Content")
            assert success is True
            assert test_file.read_text() == "New Content"
            
            # Test read_bytes - access descriptor from class
            test_file.write_bytes(b"\x00\x01\x02")
            data = FileHandler.path.read_bytes(handler)
            assert data == b"\x00\x01\x02"
    
    def test_parse_callback(self):
        """Test automatic file parsing with callback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create JSON file
            json_file = PathLib(tmpdir) / "config.json"
            json_file.write_text('{"key": "value"}')
            
            # Define parse callback
            def parse_json(path: PathLib) -> dict:
                import json
                return json.loads(path.read_text())
            
            @dataclassy
            class ConfigLoader:
                config_path: Path = Path(parse_callback=parse_json)
            
            loader = ConfigLoader(str(json_file))
            
            # Check parsed data is stored
            assert hasattr(loader, 'config_path_data')
            assert loader.config_path_data == {"key": "value"}
    
    def test_path_with_dataclassy_features(self):
        """Test Path field works with dataclassy features."""
        @dataclassy
        class ProjectConfig:
            name: str
            root_dir: Path = Path(is_dir=True)
            config_file: Path = Path(extensions=['.json', '.yaml'])
        
        # Test from_dict
        data = {
            "name": "MyProject",
            "root_dir": "/tmp/project",
            "config_file": "/tmp/project/config.json"
        }
        
        config = ProjectConfig.from_dict(data)
        assert config.name == "MyProject"
        assert isinstance(config.root_dir, PathLib)
        assert isinstance(config.config_file, PathLib)
    
    def test_invalid_path_types(self):
        """Test invalid types for Path field."""
        @dataclassy
        class BadPath:
            path: Path = Path()
        
        # Invalid type
        with pytest.raises(TypeError, match="must be a string or Path"):
            BadPath(12345)
        
        with pytest.raises(TypeError):
            BadPath(["not", "a", "path"])


class TestValidatorDescriptor:
    """Test the base Validator descriptor functionality."""
    
    def test_descriptor_protocol(self):
        """Test descriptor protocol implementation."""
        @dataclassy
        class Container:
            color: Color = Color()
        
        # Access on class returns descriptor
        assert isinstance(Container.color, Color)
        
        # Access on instance returns value
        c = Container("#FF0000")
        assert c.color == "#FF0000"
        
        # Setting works
        c.color = "blue"
        assert c.color == "#0000FF"
        
        # None is allowed
        c.color = None
        assert c.color is None
    
    def test_validator_with_inheritance(self):
        """Test validators work with inheritance."""
        @dataclassy
        class Base:
            base_color: Color = Color()
        
        @dataclassy
        class Derived(Base):
            derived_path: Path = Path()
        
        d = Derived("red", "/tmp/file")
        assert d.base_color == "#FF0000"
        assert isinstance(d.derived_path, PathLib)
    
    def test_multiple_validators_same_class(self):
        """Test multiple validator fields in same class."""
        @dataclassy
        class MultiField:
            primary: Color = Color()
            secondary: Color = Color()
            config: Path = Path()
            output: Path = Path()
        
        mf = MultiField("red", "green", "/tmp/in", "/tmp/out")
        assert mf.primary == "#FF0000"
        assert mf.secondary == "#00FF00"
        assert str(mf.config).endswith("tmp/in")  # Handle macOS /tmp resolution
        assert str(mf.output).endswith("tmp/out")  # Handle macOS /tmp resolution
        
        # Fields should be independent
        mf.primary = "blue"
        assert mf.primary == "#0000FF"
        assert mf.secondary == "#00FF00"  # Unchanged