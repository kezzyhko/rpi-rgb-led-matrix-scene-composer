"""Test components for validating the rendering pipeline."""

import math
import sys
import os

# Add parent directory to path so we can import matrix_scene_composer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import Component, RenderBuffer, cache_with_dict
from matrix_scene_composer.component import DEBUG
from typing import Tuple


class TriangleComponent(Component):
    """Renders a static filled triangle."""

    def __init__(self, scene, size: int, color: Tuple[int, int, int]):
        """
        Initialize triangle component.

        Args:
            scene: Parent scene
            size: Triangle size (width and height)
            color: RGB color tuple
        """
        super().__init__(scene)
        self._width = size
        self._height = size
        self.color = color

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def compute_state(self, time: float) -> dict:
        """Compute state - static, so state doesn't change with time."""
        return {
            'size': self._width,
            'color': self.color
        }

    def render(self, time: float) -> RenderBuffer:
        """Render triangle."""
        if DEBUG:
            print(f"  TriangleComponent.render(time={time:.2f})")
        state = self.compute_state(time)
        return self._render_cached(state)

    @cache_with_dict(maxsize=1)  # Static component, only one state
    def _render_cached(self, state) -> RenderBuffer:
        """Cached rendering of triangle."""
        buffer = RenderBuffer(self._width, self._height)
        size = state['size']
        color = state['color']

        # Draw upward-pointing triangle
        for y in range(size):
            # Width of triangle at this y level (wider at bottom)
            row_width = int((y / size) * size)
            left_edge = (size - row_width) // 2
            right_edge = left_edge + row_width

            for x in range(left_edge, right_edge):
                buffer.set_pixel(x, size - 1 - y, color)  # Flip y to point up

        return buffer


class AnimatedSquareComponent(Component):
    """Square that cycles through colors over time."""

    def __init__(self, scene, size: int, cycle_duration: float = 2.0):
        """
        Initialize animated square component.

        Args:
            scene: Parent scene
            size: Square size (width and height)
            cycle_duration: Time in seconds for one complete color cycle
        """
        super().__init__(scene)
        self._width = size
        self._height = size
        self.cycle_duration = cycle_duration

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def compute_state(self, time: float) -> dict:
        """Compute state based on time - color cycles."""
        # Calculate cycle position (0.0 to 1.0)
        t = (time % self.cycle_duration) / self.cycle_duration

        # Generate RGB values using sinusoidal cycling
        # Phase shifted by 120 degrees (2π/3) for each color
        r = int(127.5 + 127.5 * math.sin(t * 2 * math.pi))
        g = int(127.5 + 127.5 * math.sin(t * 2 * math.pi + 2.094))  # +120°
        b = int(127.5 + 127.5 * math.sin(t * 2 * math.pi + 4.189))  # +240°

        return {
            'size': self._width,
            'color': (r, g, b),
            'cycle_phase': round(t, 2)  # Round for cache efficiency
        }

    def render(self, time: float) -> RenderBuffer:
        """Render square with current color."""
        if DEBUG:
            print(f"  AnimatedSquareComponent.render(time={time:.2f})")
        state = self.compute_state(time)
        if DEBUG:
            print(f"    State: {state}")
        return self._render_cached(state)

    @cache_with_dict(maxsize=100)  # Cache multiple color variations
    def _render_cached(self, state) -> RenderBuffer:
        """Cached rendering of square."""
        buffer = RenderBuffer(self._width, self._height)
        color = state['color']

        # Fill entire square with current color
        for y in range(self._height):
            for x in range(self._width):
                buffer.set_pixel(x, y, color)

        return buffer


if __name__ == "__main__":
    # Quick test
    from matrix_scene_composer import Orchestrator, Scene

    print("Testing components...")

    orch = Orchestrator(width=64, height=32, fps=10)
    scene = Scene(orch, width=64, height=32)

    # Add triangle
    triangle = TriangleComponent(scene, size=10, color=(255, 0, 0))
    scene.add_component('triangle', triangle, position=(5, 5))

    # Add animated square
    square = AnimatedSquareComponent(scene, size=8, cycle_duration=3.0)
    scene.add_component('square', square, position=(18, 12))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    # Render a few frames
    for i in range(5):
        buffer = orch.render_single_frame(i * 0.1)
        print(f"Frame {i}: rendered {buffer.width}x{buffer.height} buffer")

    print("Components test passed!")
