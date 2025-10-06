"""Demo of dataclassy field types."""

import tempfile
from pathlib import Path as PathLib

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(PathLib(__file__).parent.parent / "src"))

from dataclassy import dataclassy, Color, Path


@dataclassy
class Theme:
    """Website theme configuration."""
    name: str
    primary_color: Color = Color()
    secondary_color: Color = Color()
    accent_color: Color = Color()
    logo_path: Path = Path(extensions=['.png', '.jpg', '.svg'], must_exist=False)


@dataclassy
class ProjectConfig:
    """Project configuration with paths."""
    project_name: str
    root_dir: Path = Path(must_exist=True, is_dir=True)
    config_file: Path = Path(extensions=['.json', '.yaml'], must_exist=True)
    output_dir: Path = Path(create_parents=True, is_dir=True)
    readme: Path = Path(extensions=['.md', '.rst'], resolve=True)


def demo_color_field():
    """Demonstrate Color field functionality."""
    print("=== Color Field Demo ===\n")
    
    # Create theme with various color formats
    theme = Theme(
        name="Ocean",
        primary_color="#0066CC",      # Hex with #
        secondary_color="FF8800",      # Hex without #
        accent_color=(64, 192, 255),   # RGB tuple
        logo_path="/tmp/logo.png"      # Required field
    )
    
    print(f"Theme: {theme.name}")
    print(f"Primary: {theme.primary_color}")
    print(f"Secondary: {theme.secondary_color}")
    print(f"Accent: {theme.accent_color}")
    
    # Use named colors
    theme2 = Theme(
        name="Forest",
        primary_color="darkgreen",
        secondary_color="brown",
        accent_color="gold",
        logo_path="/tmp/forest.svg"
    )
    
    print(f"\nTheme: {theme2.name}")
    print(f"Primary: {theme2.primary_color}")
    print(f"Secondary: {theme2.secondary_color}")
    print(f"Accent: {theme2.accent_color}")
    
    # Convert to RGB
    print(f"\nPrimary RGB: {Theme.primary_color.to_rgb(theme2)}")
    print(f"Primary CSS: {Theme.primary_color.to_css(theme2)}")
    
    # Test from_dict
    theme_data = {
        "name": "Sunset",
        "primary_color": "orange",
        "secondary_color": "#FF1493",
        "accent_color": [255, 215, 0],  # RGB as list
        "logo_path": "/tmp/sunset.jpg"
    }
    
    theme3 = Theme.from_dict(theme_data)
    print(f"\nFrom dict - Theme: {theme3.name}")
    print(f"Colors: {theme3.primary_color}, {theme3.secondary_color}, {theme3.accent_color}")


def demo_path_field():
    """Demonstrate Path field functionality."""
    print("\n\n=== Path Field Demo ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        project_dir = PathLib(tmpdir) / "myproject"
        project_dir.mkdir()
        
        config_file = project_dir / "config.json"
        config_file.write_text('{"version": "1.0"}')
        
        readme_file = project_dir / "README.md"
        readme_file.write_text("# My Project\n\nThis is a test project.")
        
        # Create project config
        config = ProjectConfig(
            project_name="TestProject",
            root_dir=str(project_dir),
            config_file=str(config_file),
            output_dir=str(project_dir / "build" / "output"),  # Will be created
            readme=str(readme_file)
        )
        
        print(f"Project: {config.project_name}")
        print(f"Root: {config.root_dir}")
        print(f"Config: {config.config_file}")
        print(f"Output: {config.output_dir}")
        print(f"Output exists: {config.output_dir.exists()}")  # True - was created
        
        # Read file contents
        readme_content = ProjectConfig.readme.read_text(config)
        print(f"\nReadme preview: {readme_content[:30]}...")
        
        # Test path validation
        try:
            bad_config = ProjectConfig(
                project_name="Bad",
                root_dir="/nonexistent",
                config_file=str(config_file),
                output_dir=str(tmpdir),
                readme=str(readme_file)
            )
        except ValueError as e:
            print(f"\nValidation error: {e}")
        
        # Test from_dict
        config_data = {
            "project_name": "FromDict",
            "root_dir": str(project_dir),
            "config_file": str(config_file),
            "output_dir": str(project_dir / "dist"),
            "readme": "README.md"  # Relative path
        }
        
        config2 = ProjectConfig.from_dict(config_data)
        print(f"\nFrom dict - Project: {config2.project_name}")
        print(f"Readme resolved to: {config2.readme}")


def demo_parse_callback():
    """Demonstrate Path field with parse callback."""
    print("\n\n=== Parse Callback Demo ===\n")
    
    import json
    
    def parse_json_config(path: PathLib) -> dict:
        """Parse JSON configuration file."""
        return json.loads(path.read_text())
    
    @dataclassy
    class AppConfig:
        name: str
        settings_file: Path = Path(
            extensions=['.json'],
            parse_callback=parse_json_config
        )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config file
        settings_path = PathLib(tmpdir) / "settings.json"
        settings_path.write_text(json.dumps({
            "debug": True,
            "port": 8080,
            "features": ["auth", "api", "admin"]
        }, indent=2))
        
        # Create app config
        app = AppConfig("MyApp", str(settings_path))
        
        print(f"App: {app.name}")
        print(f"Settings file: {app.settings_file}")
        
        # Parsed data is available
        print(f"Parsed settings: {app._settings_file_data}")
        print(f"Debug mode: {app._settings_file_data['debug']}")
        print(f"Port: {app._settings_file_data['port']}")
        print(f"Features: {', '.join(app._settings_file_data['features'])}")


if __name__ == "__main__":
    demo_color_field()
    demo_path_field()
    demo_parse_callback()