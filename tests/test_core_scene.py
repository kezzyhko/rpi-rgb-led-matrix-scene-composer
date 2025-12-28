#!/usr/bin/env python3
"""Test core Scene functionality.

Tests Scene.py core concepts:
- Component positioning and blitting
- Z-index layering (render order)
- add_component() / remove_component()
- Scene canvas rendering
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


def test_component_positioning():
    """Test that components are positioned correctly on scene canvas."""
    print("\n=== Test: Component Positioning ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Create red component at (10, 5)
    red_comp = ColorComponent(scene, 5, 3, (255, 0, 0))
    scene.add_component('red', red_comp, position=(10, 5))

    # Create green component at (20, 15)
    green_comp = ColorComponent(scene, 4, 4, (0, 255, 0))
    scene.add_component('green', green_comp, position=(20, 15))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    buffer = orch.render_single_frame(0.0)

    # Verify red component at correct position
    assert buffer.get_pixel(10, 5) == (255, 0, 0), "Red component top-left should be red"
    assert buffer.get_pixel(14, 7) == (255, 0, 0), "Red component bottom-right should be red"
    assert buffer.get_pixel(9, 5) == (0, 0, 0), "Pixel left of red should be black"

    # Verify green component at correct position
    assert buffer.get_pixel(20, 15) == (0, 255, 0), "Green component top-left should be green"
    assert buffer.get_pixel(23, 18) == (0, 255, 0), "Green component bottom-right should be green"
    assert buffer.get_pixel(19, 15) == (0, 0, 0), "Pixel left of green should be black"

    print("✓ Components positioned correctly")
    print(f"✓ Red component at (10, 5) size 5x3")
    print(f"✓ Green component at (20, 15) size 4x4")


def test_z_index_layering():
    """Test that z-index controls render order (higher z-index renders on top)."""
    print("\n=== Test: Z-Index Layering ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Create overlapping components
    # Red 10x10 at (5, 5) with z-index 1
    red_comp = ColorComponent(scene, 10, 10, (255, 0, 0))
    scene.add_component('red', red_comp, position=(5, 5), z_index=1)

    # Blue 10x10 at (10, 10) with z-index 2 (should render on top)
    blue_comp = ColorComponent(scene, 10, 10, (0, 0, 255))
    scene.add_component('blue', blue_comp, position=(10, 10), z_index=2)

    orch.add_scene('test', scene)
    orch.transition_to('test')

    buffer = orch.render_single_frame(0.0)

    # Check overlap region (10-15, 10-15)
    # Blue should be on top because z-index 2 > 1
    assert buffer.get_pixel(12, 12) == (0, 0, 255), "Overlap should show blue (higher z-index)"

    # Check non-overlap regions
    assert buffer.get_pixel(7, 7) == (255, 0, 0), "Red-only area should be red"
    assert buffer.get_pixel(17, 17) == (0, 0, 255), "Blue-only area should be blue"

    print("✓ Z-index layering works correctly")
    print("✓ Higher z-index renders on top in overlap regions")


def test_add_remove_component():
    """Test adding and removing components from scene."""
    print("\n=== Test: Add/Remove Component ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Add red component
    red_comp = ColorComponent(scene, 5, 5, (255, 0, 0))
    scene.add_component('red', red_comp, position=(10, 10))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    # Render with component
    buffer1 = orch.render_single_frame(0.0)
    assert buffer1.get_pixel(12, 12) == (255, 0, 0), "Red component should be visible"

    # Remove component
    scene.remove_component('red')

    # Render without component
    buffer2 = orch.render_single_frame(0.0)
    assert buffer2.get_pixel(12, 12) == (0, 0, 0), "Red component should be gone"

    # Re-add component (different position)
    scene.add_component('red', red_comp, position=(20, 20))

    # Render with component at new position
    buffer3 = orch.render_single_frame(0.0)
    assert buffer3.get_pixel(12, 12) == (0, 0, 0), "Old position should be black"
    assert buffer3.get_pixel(22, 22) == (255, 0, 0), "New position should be red"

    print("✓ add_component() works correctly")
    print("✓ remove_component() works correctly")
    print("✓ Re-adding component at different position works")


def test_scene_canvas_size():
    """Test that scene respects canvas size boundaries."""
    print("\n=== Test: Scene Canvas Size ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Add component that extends beyond canvas
    large_comp = ColorComponent(scene, 20, 20, (255, 0, 0))
    scene.add_component('large', large_comp, position=(55, 25))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    buffer = orch.render_single_frame(0.0)

    # Component should be clipped to canvas boundaries
    # Position (55, 25) with size 20x20 would go to (75, 45)
    # But canvas is only 64x32, so should clip

    assert buffer.get_pixel(60, 30) == (255, 0, 0), "Should render within canvas"
    assert buffer.width == 64, "Buffer width should match canvas"
    assert buffer.height == 32, "Buffer height should match canvas"

    print("✓ Scene respects canvas boundaries")
    print("✓ Components clipped correctly when extending beyond canvas")


def test_multiple_components():
    """Test scene with multiple components at various positions."""
    print("\n=== Test: Multiple Components ===")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Add multiple components
    scene.add_component('red', ColorComponent(scene, 5, 5, (255, 0, 0)), position=(0, 0))
    scene.add_component('green', ColorComponent(scene, 5, 5, (0, 255, 0)), position=(10, 0))
    scene.add_component('blue', ColorComponent(scene, 5, 5, (0, 0, 255)), position=(0, 10))
    scene.add_component('yellow', ColorComponent(scene, 5, 5, (255, 255, 0)), position=(10, 10))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    buffer = orch.render_single_frame(0.0)

    # Verify all components rendered correctly
    assert buffer.get_pixel(2, 2) == (255, 0, 0), "Red at (0, 0)"
    assert buffer.get_pixel(12, 2) == (0, 255, 0), "Green at (10, 0)"
    assert buffer.get_pixel(2, 12) == (0, 0, 255), "Blue at (0, 10)"
    assert buffer.get_pixel(12, 12) == (255, 255, 0), "Yellow at (10, 10)"

    print("✓ Multiple components render correctly")
    print("✓ Each component maintains independent position")


if __name__ == "__main__":
    test_component_positioning()
    test_z_index_layering()
    test_add_remove_component()
    test_scene_canvas_size()
    test_multiple_components()

    print("\n" + "="*50)
    print("SCENE CORE TESTS PASSED")
    print("="*50)
    print("✓ Component positioning works correctly")
    print("✓ Z-index layering controls render order")
    print("✓ add_component() / remove_component() work")
    print("✓ Scene respects canvas boundaries")
    print("✓ Multiple components render independently")
    print()
