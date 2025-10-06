"""Color field type for dataclassy."""

import re
from typing import Any, Tuple

from .validators import Validator


class Color(Validator):
    """
    Field type that accepts and validates color values.

    Accepts:
    - Hex strings: "#FF0000", "#F00", "FF0000", "F00"
    - RGB tuples: (255, 0, 0)
    - Named colors: "red", "green", "blue", etc.

    Always stores colors as uppercase hex strings (e.g., "#FF0000").
    """

    # Common named colors
    NAMED_COLORS = {
        # Basic colors
        "black": "#000000",
        "white": "#FFFFFF",
        "red": "#FF0000",
        "green": "#00FF00",
        "blue": "#0000FF",
        "yellow": "#FFFF00",
        "cyan": "#00FFFF",
        "magenta": "#FF00FF",
        # Extended colors
        "orange": "#FFA500",
        "purple": "#800080",
        "brown": "#A52A2A",
        "pink": "#FFC0CB",
        "gray": "#808080",
        "grey": "#808080",
        "lime": "#00FF00",
        "navy": "#000080",
        "olive": "#808000",
        "teal": "#008080",
        "silver": "#C0C0C0",
        "gold": "#FFD700",
        "maroon": "#800000",
        "indigo": "#4B0082",
        "violet": "#EE82EE",
        "coral": "#FF7F50",
        "salmon": "#FA8072",
        "khaki": "#F0E68C",
        "crimson": "#DC143C",
        "fuchsia": "#FF00FF",
        "lavender": "#E6E6FA",
        "plum": "#DDA0DD",
        "turquoise": "#40E0D0",
        "tan": "#D2B48C",
        "skyblue": "#87CEEB",
        "darkblue": "#00008B",
        "darkgreen": "#006400",
        "darkred": "#8B0000",
        "lightblue": "#ADD8E6",
        "lightgreen": "#90EE90",
        "lightgray": "#D3D3D3",
        "lightgrey": "#D3D3D3",
    }

    def convert(self, value: Any) -> str:
        """
        Convert various color formats to hex string.

        Args:
            value: Color value (hex string, RGB tuple, or color name)

        Returns:
            Uppercase hex color string (e.g., "#FF0000")
        """
        if isinstance(value, str):
            # Check if it's a named color
            lower_value = value.lower()
            if lower_value in self.NAMED_COLORS:
                return self.NAMED_COLORS[lower_value]

            # Process hex string
            hex_value = value.strip()

            # Add # prefix if missing
            if not hex_value.startswith("#"):
                hex_value = "#" + hex_value

            # Convert 3-digit hex to 6-digit
            if len(hex_value) == 4:  # #RGB
                hex_value = "#" + "".join(c * 2 for c in hex_value[1:])

            return hex_value.upper()

        elif isinstance(value, (tuple, list)):
            if len(value) != 3:
                # Wrong number of values, let validation catch it
                return value
            # Convert RGB tuple to hex
            try:
                r, g, b = value
                # Ensure values are integers in valid range
                r = max(0, min(255, int(r)))
                g = max(0, min(255, int(g)))
                b = max(0, min(255, int(b)))
                return f"#{r:02X}{g:02X}{b:02X}"
            except (ValueError, TypeError):
                # If conversion fails, return as-is for validation to catch
                return value

        # Return as-is for validation to handle
        return value

    def validate(self, value: Any) -> None:
        """
        Validate that the value is a valid hex color.

        Args:
            value: The converted color value

        Raises:
            ValueError: If the value is not a valid hex color
            TypeError: If the value is not a string after conversion
        """
        if not isinstance(value, str):
            raise TypeError(
                f"{self.public_name} must be a color string, RGB tuple, or named color, "
                f"got {type(value).__name__}"
            )

        # Check hex format: #RRGGBB
        if not re.match(r"^#[0-9A-F]{6}$", value):
            raise ValueError(
                f"{self.public_name} must be a valid hex color (#RRGGBB), "
                f"got {value!r}"
            )

    def to_rgb(self, obj: Any) -> Tuple[int, int, int]:
        """
        Convert the color to RGB tuple.

        Args:
            obj: The instance containing this color field

        Returns:
            RGB tuple (r, g, b) with values 0-255
        """
        hex_value = self.__get__(obj)
        if hex_value is None:
            return (0, 0, 0)

        # Remove # and convert to RGB
        hex_value = hex_value.lstrip("#")
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)

        return (r, g, b)

    def to_css(self, obj: Any) -> str:
        """
        Get CSS-compatible color string.

        Args:
            obj: The instance containing this color field

        Returns:
            Lowercase hex color for CSS
        """
        value = self.__get__(obj)
        return value.lower() if value else "#000000"
