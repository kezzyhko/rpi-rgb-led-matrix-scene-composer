"""Rainbow filter component for applying rainbow gradients to other components."""

import math
from typing import Tuple
from .component import Component
from .render_buffer import RenderBuffer


class RainbowFilter(Component):
    """
    Rainbow filter that transforms colors in a source component to rainbow gradient.

    Features:
    - Wraps any other component
    - Transforms specific color (or all colors) to animated rainbow
    - Configurable direction: horizontal, vertical, diagonal
    - Configurable animation speed
    - Optional color matching with tolerance
    """

    def __init__(
        self,
        source_component: Component,
        color_key: Tuple[int, int, int] | None = None,
        match_tolerance: int = 10,
        direction: str = 'horizontal',
        speed: float = 1.0
    ):
        """
        Initialize RainbowFilter.

        Args:
            source_component: Component to apply rainbow filter to
            color_key: Color to transform (None = transform all non-black pixels)
            match_tolerance: How close colors need to match color_key (0-255)
            direction: Rainbow direction ('horizontal', 'vertical', 'diagonal')
            speed: Animation speed in cycles per second
        """
        super().__init__()

        self.source_component = source_component
        self.color_key = color_key
        self.match_tolerance = match_tolerance
        self.direction = direction
        self.speed = speed

    @property
    def width(self) -> int:
        return self.source_component.width

    @property
    def height(self) -> int:
        return self.source_component.height

    def compute_state(self, time: float) -> dict:
        """Compute state - includes time for animation."""
        return {
            'source_state': self.source_component.compute_state(time),
            'time': time,
            'speed': self.speed,
            'direction': self.direction
        }

    def render(self, time: float) -> RenderBuffer:
        """Render filtered component."""
        # Get source buffer
        source_buffer = self.source_component.render(time)

        # Create output buffer
        output_buffer = RenderBuffer(source_buffer.width, source_buffer.height)

        # Apply rainbow transformation
        for y in range(source_buffer.height):
            for x in range(source_buffer.width):
                source_color = source_buffer.get_pixel(x, y)

                # Check if this pixel should be transformed
                if self._should_transform(source_color):
                    # Calculate rainbow color based on position and time
                    rainbow_color = self._get_rainbow_color(x, y, time)
                    output_buffer.set_pixel(x, y, rainbow_color)
                else:
                    # Keep original color
                    output_buffer.set_pixel(x, y, source_color)

        return output_buffer

    def _should_transform(self, color: Tuple[int, int, int]) -> bool:
        """Check if a color should be transformed to rainbow."""
        # If no color_key specified, transform all non-black pixels
        if self.color_key is None:
            return color != (0, 0, 0)

        # Check if color matches color_key within tolerance
        # Convert to int to avoid numpy overflow warnings
        r, g, b = int(color[0]), int(color[1]), int(color[2])
        kr, kg, kb = self.color_key

        distance = math.sqrt(
            (r - kr) ** 2 +
            (g - kg) ** 2 +
            (b - kb) ** 2
        )

        return distance <= self.match_tolerance

    def _get_rainbow_color(
        self,
        x: int,
        y: int,
        time: float
    ) -> Tuple[int, int, int]:
        """Calculate rainbow color for a pixel based on position and time."""
        # Calculate position factor based on direction
        if self.direction == 'horizontal':
            position_factor = x / max(self.width - 1, 1)
        elif self.direction == 'vertical':
            position_factor = y / max(self.height - 1, 1)
        elif self.direction == 'diagonal':
            position_factor = (x + y) / max(self.width + self.height - 2, 1)
        else:
            position_factor = 0

        # Add time animation
        hue = (position_factor + (time * self.speed)) % 1.0

        # Convert HSV to RGB (S=1, V=1 for full saturation rainbow)
        return self._hsv_to_rgb(hue, 1.0, 1.0)

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV color to RGB tuple."""
        if s == 0.0:
            r = g = b = v
        else:
            i = int(h * 6.0)
            f = (h * 6.0) - i
            p = v * (1.0 - s)
            q = v * (1.0 - s * f)
            t = v * (1.0 - s * (1.0 - f))
            i = i % 6

            if i == 0:
                r, g, b = v, t, p
            elif i == 1:
                r, g, b = q, v, p
            elif i == 2:
                r, g, b = p, v, t
            elif i == 3:
                r, g, b = p, q, v
            elif i == 4:
                r, g, b = t, p, v
            else:
                r, g, b = v, p, q

        return (
            int(r * 255),
            int(g * 255),
            int(b * 255)
        )
