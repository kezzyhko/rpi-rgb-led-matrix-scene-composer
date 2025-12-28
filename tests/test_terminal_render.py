#!/usr/bin/env python3
"""Test rendering pipeline with terminal output."""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import Orchestrator, Scene
from test_components import TriangleComponent, AnimatedSquareComponent


def render_to_terminal(buffer):
    """Render numpy RGB array to terminal with true colors."""
    # Clear screen and move cursor to top-left
    print("\033[2J\033[H", end='')

    height, width, _ = buffer.data.shape

    for y in range(height):
        for x in range(width):
            r, g, b = buffer.data[y, x]
            # Use colored block character
            print(f'\033[38;2;{r};{g};{b}m█\033[0m', end='')
        print()  # Newline after each row


if __name__ == "__main__":
    print("Starting rendering test...")
    print("Press Ctrl+C to exit\n")
    time.sleep(1)

    # Create orchestrator (64x32: 32 rows x 64 columns)
    orch = Orchestrator(width=64, height=32, fps=2)  # 2 FPS for easy visual validation

    # Set terminal display callback
    orch.set_display_callback(render_to_terminal)

    # Create scene
    scene = Scene(orch, width=64, height=32)

    # Add static red triangle
    triangle = TriangleComponent(scene, size=12, color=(255, 0, 0))
    scene.add_component('triangle', triangle, position=(5, 10), z_index=1)

    # Add animated color-cycling square (slow 10 second cycle)
    square = AnimatedSquareComponent(scene, size=10, cycle_duration=10.0)
    scene.add_component('square', square, position=(40, 8), z_index=2)

    # Register scene
    orch.add_scene('test_scene', scene)
    orch.transition_to('test_scene')

    # Start render loop (10 seconds to see full color cycle)
    orch.start(duration=10.0)

    print("\n\nRendering complete!")
