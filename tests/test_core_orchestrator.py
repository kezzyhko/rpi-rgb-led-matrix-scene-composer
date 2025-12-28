#!/usr/bin/env python3
"""Test core Orchestrator functionality.

Tests Orchestrator.py core concepts:
- Scene management (add_scene, transition_to)
- Frame rendering (render_single_frame)
- Scene transitions
- FPS timing behavior
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import Component, RenderBuffer, Scene, Orchestrator


class ColorComponent(Component):
    """Simple component that fills with a solid color."""

    def __init__(self, scene, width: int, height: int, color: tuple):
        super().__init__(scene)
        self._width = width
        self._height = height
        self.color = color

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def compute_state(self, time: float) -> dict:
        return {'color': self.color}

    def render(self, time: float) -> RenderBuffer:
        buffer = RenderBuffer(self._width, self._height)
        for y in range(self._height):
            for x in range(self._width):
                buffer.set_pixel(x, y, self.color)
        return buffer


def test_scene_management():
    """Test adding and transitioning between scenes."""
    print("\n=== Test: Scene Management ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)

    # Create two scenes with different colors
    scene1 = Scene(orch, width=width, height=height)
    scene1.add_component('red', ColorComponent(scene1, 10, 10, (255, 0, 0)), position=(0, 0))

    scene2 = Scene(orch, width=width, height=height)
    scene2.add_component('blue', ColorComponent(scene2, 10, 10, (0, 0, 255)), position=(0, 0))

    # Add scenes to orchestrator
    orch.add_scene('scene1', scene1)
    orch.add_scene('scene2', scene2)

    # Transition to scene1
    orch.transition_to('scene1')
    buffer1 = orch.render_single_frame(0.0)
    assert buffer1.get_pixel(5, 5) == (255, 0, 0), "Should show scene1 (red)"

    # Transition to scene2
    orch.transition_to('scene2')
    buffer2 = orch.render_single_frame(0.0)
    assert buffer2.get_pixel(5, 5) == (0, 0, 255), "Should show scene2 (blue)"

    # Transition back to scene1
    orch.transition_to('scene1')
    buffer3 = orch.render_single_frame(0.0)
    assert buffer3.get_pixel(5, 5) == (255, 0, 0), "Should show scene1 (red) again"

    print("✓ add_scene() works correctly")
    print("✓ transition_to() switches active scene")
    print("✓ Can transition between multiple scenes")


def test_render_single_frame():
    """Test single frame rendering with time parameter."""
    print("\n=== Test: Render Single Frame ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)

    scene = Scene(orch, width=width, height=height)
    scene.add_component('test', ColorComponent(scene, 10, 10, (128, 128, 128)), position=(5, 5))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    # Render at different times
    buffer1 = orch.render_single_frame(0.0)
    buffer2 = orch.render_single_frame(1.0)
    buffer3 = orch.render_single_frame(2.5)

    # All should render successfully
    assert buffer1.width == 64 and buffer1.height == 32
    assert buffer2.width == 64 and buffer2.height == 32
    assert buffer3.width == 64 and buffer3.height == 32

    # Component should be visible in all frames
    assert buffer1.get_pixel(7, 7) == (128, 128, 128)
    assert buffer2.get_pixel(7, 7) == (128, 128, 128)
    assert buffer3.get_pixel(7, 7) == (128, 128, 128)

    print("✓ render_single_frame() works at different times")
    print("✓ Buffer dimensions match orchestrator dimensions")


def test_orchestrator_dimensions():
    """Test that orchestrator enforces canvas dimensions."""
    print("\n=== Test: Orchestrator Dimensions ===")

    # Create orchestrators with different sizes
    orch_small = Orchestrator(width=32, height=16, fps=10)
    orch_large = Orchestrator(width=128, height=64, fps=10)

    scene_small = Scene(orch_small, width=32, height=16)
    scene_small.add_component('test', ColorComponent(scene_small, 5, 5, (255, 255, 255)), position=(0, 0))

    scene_large = Scene(orch_large, width=128, height=64)
    scene_large.add_component('test', ColorComponent(scene_large, 5, 5, (255, 255, 255)), position=(0, 0))

    orch_small.add_scene('test', scene_small)
    orch_small.transition_to('test')

    orch_large.add_scene('test', scene_large)
    orch_large.transition_to('test')

    buffer_small = orch_small.render_single_frame(0.0)
    buffer_large = orch_large.render_single_frame(0.0)

    assert buffer_small.width == 32 and buffer_small.height == 16
    assert buffer_large.width == 128 and buffer_large.height == 64

    print("✓ Orchestrator respects custom dimensions")
    print("✓ Small canvas: 32x16")
    print("✓ Large canvas: 128x64")


def test_fps_setting():
    """Test that FPS setting is stored correctly."""
    print("\n=== Test: FPS Setting ===")

    orch1 = Orchestrator(width=64, height=32, fps=10)
    orch2 = Orchestrator(width=64, height=32, fps=60)
    orch3 = Orchestrator(width=64, height=32, fps=120)

    assert orch1.fps == 10, "FPS should be 10"
    assert orch2.fps == 60, "FPS should be 60"
    assert orch3.fps == 120, "FPS should be 120"

    print("✓ FPS setting stored correctly")
    print(f"✓ Tested FPS values: 10, 60, 120")


def test_no_scene_rendering():
    """Test behavior when no scene is active."""
    print("\n=== Test: No Scene Rendering ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)

    # Don't add any scenes or transition

    # Should return black buffer
    buffer = orch.render_single_frame(0.0)

    assert buffer.width == 64 and buffer.height == 32

    # Check a few pixels - should all be black
    assert buffer.get_pixel(0, 0) == (0, 0, 0)
    assert buffer.get_pixel(32, 16) == (0, 0, 0)
    assert buffer.get_pixel(63, 31) == (0, 0, 0)

    print("✓ Renders black buffer when no scene active")


def test_scene_without_components():
    """Test rendering empty scene (no components)."""
    print("\n=== Test: Scene Without Components ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)

    scene = Scene(orch, width=width, height=height)
    # Don't add any components

    orch.add_scene('empty', scene)
    orch.transition_to('empty')

    buffer = orch.render_single_frame(0.0)

    assert buffer.width == 64 and buffer.height == 32

    # Should be all black
    assert buffer.get_pixel(32, 16) == (0, 0, 0)

    print("✓ Empty scene renders as black buffer")


def test_multiple_scenes():
    """Test orchestrator with many scenes."""
    print("\n=== Test: Multiple Scenes ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)

    # Create 5 different scenes
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
    ]

    for i, color in enumerate(colors):
        scene = Scene(orch, width=width, height=height)
        scene.add_component('comp', ColorComponent(scene, 10, 10, color), position=(5, 5))
        orch.add_scene(f'scene{i}', scene)

    # Transition through all scenes
    for i, expected_color in enumerate(colors):
        orch.transition_to(f'scene{i}')
        buffer = orch.render_single_frame(0.0)
        actual_color = buffer.get_pixel(7, 7)
        assert actual_color == expected_color, f"Scene {i} should show {expected_color}"

    print("✓ Can manage multiple scenes")
    print(f"✓ Tested with {len(colors)} different scenes")


if __name__ == "__main__":
    test_scene_management()
    test_render_single_frame()
    test_orchestrator_dimensions()
    test_fps_setting()
    test_no_scene_rendering()
    test_scene_without_components()
    test_multiple_scenes()

    print("\n" + "="*50)
    print("ORCHESTRATOR CORE TESTS PASSED")
    print("="*50)
    print("✓ Scene management (add_scene, transition_to)")
    print("✓ Frame rendering (render_single_frame)")
    print("✓ Orchestrator dimensions enforcement")
    print("✓ FPS setting storage")
    print("✓ Edge cases (no scene, empty scene)")
    print("✓ Multiple scene handling")
    print()
