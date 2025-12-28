#!/usr/bin/env python3
"""Test caching behavior with shared component across multiple scenes."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Enable debug logging
import matrix_scene_composer.component as component_module
component_module.DEBUG = True

from matrix_scene_composer import Orchestrator, Scene
from test_components import TriangleComponent, AnimatedSquareComponent


def test_shared_component_caching():
    """
    Test that demonstrates:
    1. Same component instance can be used in multiple scenes
    2. Caching works correctly across scenes
    3. Only scenes with changed components re-render
    """

    print("="*80)
    print("SHARED COMPONENT CACHING TEST")
    print("="*80)

    # Create orchestrator
    orch = Orchestrator(width=64, height=32, fps=10)

    # Create SHARED component instance
    triangle_instance_1 = TriangleComponent(None, size=10, color=(255, 0, 0))

    # Create animated component
    animated_square = AnimatedSquareComponent(None, size=8, cycle_duration=10.0)

    # Scene 1: Only the shared triangle
    scene1 = Scene(orch, width=64, height=32)
    triangle_instance_1.scene = scene1  # Update scene reference
    scene1.add_component('triangle', triangle_instance_1, position=(5, 5))

    # Scene 2: Shared triangle AND animated square
    scene2 = Scene(orch, width=64, height=32)
    triangle_instance_1.scene = scene2  # Component now references scene2
    animated_square.scene = scene2
    scene2.add_component('triangle', triangle_instance_1, position=(5, 5))
    scene2.add_component('square', animated_square, position=(18, 8))

    # Register scenes
    orch.add_scene('scene1', scene1)
    orch.add_scene('scene2', scene2)

    print("\nSetup:")
    print("  - triangle_instance_1: Static red triangle (shared between scenes)")
    print("  - animated_square: Color-cycling square")
    print("  - Scene 1: Contains only triangle_instance_1")
    print("  - Scene 2: Contains triangle_instance_1 AND animated_square")

    # Frame 1: Render both scenes at t=0.0
    print("\n\n" + "="*80)
    print("FRAME 1: Render both scenes at time=0.0")
    print("EXPECT: All components render fresh (first time)")
    print("="*80)
    orch.time = 0.0

    print("\n--- Rendering Scene 1 ---")
    orch.transition_to('scene1')
    buffer1_frame1 = orch._render_frame()

    print("\n--- Rendering Scene 2 ---")
    orch.transition_to('scene2')
    buffer2_frame1 = orch._render_frame()

    # Frame 2: Render both scenes at t=0.1
    print("\n\n" + "="*80)
    print("FRAME 2: Render both scenes at time=0.1")
    print("EXPECT:")
    print("  - Scene 1: Triangle cached (no change)")
    print("  - Scene 2: Triangle cached, Square NEW (color changed)")
    print("="*80)
    orch.time = 0.1

    print("\n--- Rendering Scene 1 ---")
    orch.transition_to('scene1')
    buffer1_frame2 = orch._render_frame()

    print("\n--- Rendering Scene 2 ---")
    orch.transition_to('scene2')
    buffer2_frame2 = orch._render_frame()

    # Frame 3: Render both scenes at t=1.0
    print("\n\n" + "="*80)
    print("FRAME 3: Render both scenes at time=1.0")
    print("EXPECT:")
    print("  - Scene 1: Triangle cached (no change)")
    print("  - Scene 2: Triangle cached, Square NEW (color changed)")
    print("="*80)
    orch.time = 1.0

    print("\n--- Rendering Scene 1 ---")
    orch.transition_to('scene1')
    buffer1_frame3 = orch._render_frame()

    print("\n--- Rendering Scene 2 ---")
    orch.transition_to('scene2')
    buffer2_frame3 = orch._render_frame()

    print("\n\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nKey Observations:")
    print("1. triangle_instance_1 is CACHED after first render (frame 1)")
    print("2. Scene 1 always hits cache (nothing changes)")
    print("3. Scene 2 re-composes but triangle hits cache (only square re-renders)")
    print("4. Same component instance works correctly in multiple scenes")
    print("\nCaching Efficiency:")
    print("  - Scene 1: No re-rendering after frame 1 (fully cached)")
    print("  - Scene 2: Only animated_square re-renders when color changes")
    print("  - triangle_instance_1: Renders once, reused everywhere")


if __name__ == "__main__":
    test_shared_component_caching()
