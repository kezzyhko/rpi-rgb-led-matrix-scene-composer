"""
Test clean architecture - components don't know about scenes.

This test defines the desired API and will fail until we refactor.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import Scene, Component, RenderBuffer


class SimpleComponent(Component):
    """Test component - standalone, no scene reference."""

    def __init__(self, width=10, height=10, color=(255, 0, 0)):
        super().__init__()
        self._width = width
        self._height = height
        self.color = color

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def compute_state(self, time):
        # Static component - state doesn't change
        return {"static": True}

    def render(self, time):
        # Component renders itself, time is passed in
        buffer = RenderBuffer(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                buffer.set_pixel(x, y, self.color)
        return buffer


class AnimatedComponent(Component):
    """Test component with animation - time-based."""

    def __init__(self, width=10, height=10):
        super().__init__()
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def compute_state(self, time):
        # State changes every second
        return {"frame": int(time)}

    def render(self, time):
        # Color cycles based on time
        r = int((time * 50) % 255)
        buffer = RenderBuffer(self.width, self.height)
        color = (r, 0, 0)
        for y in range(self.height):
            for x in range(self.width):
                buffer.set_pixel(x, y, color)
        return buffer


def test_component_standalone():
    """Components work standalone without scene."""
    comp = SimpleComponent(width=10, height=10, color=(255, 0, 0))

    # Component can render itself with time passed in
    buffer = comp.render(time=0.0)

    assert buffer.width == 10
    assert buffer.height == 10
    assert buffer.get_pixel(0, 0) == (255, 0, 0)


def test_component_no_scene_reference():
    """Components don't reference scene."""
    comp = SimpleComponent()

    # Component should NOT have scene attribute
    assert not hasattr(comp, 'scene')


def test_scene_composes_components():
    """Scene composes components - clean one-way dependency."""
    # Create components without scene reference
    red_box = SimpleComponent(width=10, height=10, color=(255, 0, 0))
    blue_box = SimpleComponent(width=10, height=10, color=(0, 0, 255))

    # Scene knows about components, not vice versa
    scene = Scene(width=32, height=32)
    scene.add_component('red', red_box, position=(0, 0))
    scene.add_component('blue', blue_box, position=(10, 10))

    # Scene renders by calling component.render(time)
    buffer = scene.render(time=0.0)

    # Verify red box rendered at (0, 0)
    assert buffer.get_pixel(0, 0) == (255, 0, 0)

    # Verify blue box rendered at (10, 10)
    assert buffer.get_pixel(10, 10) == (0, 0, 255)


def test_animated_component():
    """Animated components use time parameter."""
    comp = AnimatedComponent(width=10, height=10)

    # Render at different times
    buffer1 = comp.render(time=0.0)
    buffer2 = comp.render(time=5.0)

    # Color should be different at different times
    color1 = buffer1.get_pixel(0, 0)
    color2 = buffer2.get_pixel(0, 0)

    assert color1 != color2


def test_scene_no_orchestrator_required():
    """Scene works standalone without orchestrator."""
    scene = Scene(width=32, height=32)

    comp = SimpleComponent()
    scene.add_component('box', comp, position=(5, 5))

    # Scene can render without orchestrator
    buffer = scene.render(time=1.5)

    assert buffer.width == 32
    assert buffer.height == 32


if __name__ == "__main__":
    print("Running clean architecture tests...")

    try:
        test_component_standalone()
        print("✓ test_component_standalone")
    except AssertionError as e:
        print(f"✗ test_component_standalone: {e}")

    try:
        test_component_no_scene_reference()
        print("✓ test_component_no_scene_reference")
    except (AssertionError, AttributeError) as e:
        print(f"✗ test_component_no_scene_reference: {e}")

    try:
        test_scene_composes_components()
        print("✓ test_scene_composes_components")
    except AssertionError as e:
        print(f"✗ test_scene_composes_components: {e}")

    try:
        test_animated_component()
        print("✓ test_animated_component")
    except AssertionError as e:
        print(f"✗ test_animated_component: {e}")

    try:
        test_scene_no_orchestrator_required()
        print("✓ test_scene_no_orchestrator_required")
    except AssertionError as e:
        print(f"✗ test_scene_no_orchestrator_required: {e}")

    print("\nAll tests completed!")
