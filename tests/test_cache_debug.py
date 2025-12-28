#!/usr/bin/env python3
"""Test script to validate caching behavior with debug logging."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Enable debug logging
import matrix_scene_composer.component as component_module
component_module.DEBUG = True

from matrix_scene_composer import Orchestrator, Scene
from test_components import TriangleComponent, AnimatedSquareComponent


def test_caching():
    """Test that demonstrates caching behavior."""

    print("="*80)
    print("CACHE BEHAVIOR TEST")
    print("="*80)

    # Create orchestrator
    orch = Orchestrator(width=64, height=32, fps=10)

    # Create scene
    scene = Scene(orch, width=64, height=32)

    # Add static triangle (should cache after first render)
    triangle = TriangleComponent(scene, size=10, color=(255, 0, 0))
    scene.add_component('triangle', triangle, position=(5, 5))

    # Add animated square (should cache, but re-render when color changes)
    square = AnimatedSquareComponent(scene, size=8, cycle_duration=10.0)
    scene.add_component('square', square, position=(18, 8))

    # Register scene
    orch.add_scene('test', scene)
    orch.transition_to('test')

    print("\n\nRendering Frame 1 (time=0.0) - EXPECT: Both components render new")
    print("-" * 80)
    orch.time = 0.0
    orch._render_frame()

    print("\n\nRendering Frame 2 (time=0.1) - EXPECT: Triangle cached, Square new (color changed)")
    print("-" * 80)
    orch.time = 0.1
    orch._render_frame()

    print("\n\nRendering Frame 3 (time=0.2) - EXPECT: Triangle cached, Square cached (color same as frame 2)")
    print("-" * 80)
    orch.time = 0.2
    orch._render_frame()

    print("\n\nRendering Frame 4 (time=1.0) - EXPECT: Triangle cached, Square new (color changed)")
    print("-" * 80)
    orch.time = 1.0
    orch._render_frame()

    print("\n\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nObservations:")
    print("- TriangleComponent (static): Should always hit cache after first render")
    print("- AnimatedSquareComponent: Should re-render when color changes (phase changes)")
    print("- AnimatedSquareComponent: Should hit cache when color stays same (phase rounds to same value)")


if __name__ == "__main__":
    test_caching()
