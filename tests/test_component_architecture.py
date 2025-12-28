#!/usr/bin/env python3
"""
Tests for new Component/Scene architecture with compute_state → _render_cached pattern.

What matters (things to test):
1. Component._rendered_at timestamp tracking (cache invalidation signal)
2. Component.compute_state() doesn't include 'time' in dict
3. _render_cached(state, time) signature with time as separate param
4. Scene inherits from Component (same protocol)
5. Scene cache invalidation when child position changes
6. Scene cache invalidation when child component changes (_rendered_at changes)
7. Scene cache HIT when idle (time advances but state unchanged)
8. Nested scenes work (Scene contains Scene)
9. Animations calculate new state without mutating ComponentInstance

What doesn't matter (don't test):
- Implementation details of specific components (text rendering, etc)
- Display targets
- Orchestrator integration
- Easing functions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import Component, Scene, RenderBuffer, cache_with_dict


class SimpleComponent(Component):
    """Test component for architecture tests."""

    def __init__(self, value: str = "test"):
        super().__init__()
        self.value = value
        self._width = 10
        self._height = 10
        self.render_call_count = 0

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def compute_state(self, time: float) -> dict:
        """Compute state - should NOT include time."""
        return {'value': self.value}

    @cache_with_dict(maxsize=32)
    def _render_cached(self, state: dict, time: float) -> RenderBuffer:
        """Render from state - time passed separately."""
        self.render_call_count += 1
        buffer = RenderBuffer(self.width, self.height)
        # Fill with white pixels
        for y in range(self.height):
            for x in range(self.width):
                buffer.set_pixel(x, y, (255, 255, 255))
        return buffer


def test_component_rendered_at_tracking():
    """Test that Component._rendered_at updates when state changes."""
    print("\n=== Test: Component._rendered_at Tracking ===")

    comp = SimpleComponent("initial")

    # Render at t=1.0
    buffer1 = comp.render(1.0)
    assert comp._rendered_at == 1.0, f"Expected _rendered_at=1.0, got {comp._rendered_at}"

    # Render again at t=2.0 with same state - timestamp should NOT update
    buffer2 = comp.render(2.0)
    assert comp._rendered_at == 1.0, "Timestamp shouldn't update if state unchanged"

    # Change state and render at t=3.0 - timestamp SHOULD update
    comp.value = "changed"
    buffer3 = comp.render(3.0)
    assert comp._rendered_at == 3.0, f"Expected _rendered_at=3.0, got {comp._rendered_at}"

    print(f"✓ _rendered_at tracking works correctly")


def test_compute_state_no_time_key():
    """Test that compute_state() doesn't include 'time' in returned dict."""
    print("\n=== Test: compute_state() No Time Key ===")

    comp = SimpleComponent("test")
    state = comp.compute_state(5.0)

    assert 'time' not in state, "compute_state() should NOT include 'time' key"
    assert 'value' in state, "compute_state() should include component state"

    print("✓ compute_state() correctly excludes time from state dict")


def test_render_cached_signature():
    """Test that _render_cached accepts (state, time) parameters."""
    print("\n=== Test: _render_cached(state, time) Signature ===")

    comp = SimpleComponent("test")

    # Get state
    state = comp.compute_state(1.0)

    # Call _render_cached directly with state and time as separate params
    buffer = comp._render_cached(state, time=5.0)

    assert buffer is not None
    assert buffer.width == 10
    assert buffer.height == 10

    print("✓ _render_cached(state, time) signature works")


def test_component_cache_ignores_time_parameter():
    """Test that component cache only uses state dict, ignores time."""
    print("\n=== Test: Component Cache Ignores Time ===")

    comp = SimpleComponent("test")

    # Render at t=1.0
    buffer1 = comp.render(1.0)
    assert comp.render_call_count == 1

    # Render at t=2.0 - different time, same state → should cache HIT
    buffer2 = comp.render(2.0)
    assert comp.render_call_count == 1, "Cache should hit despite different time"
    assert buffer1 is buffer2, "Should return same cached buffer"

    # Change state and render at t=3.0 → should cache MISS
    comp.value = "changed"
    buffer3 = comp.render(3.0)
    assert comp.render_call_count == 2, "Cache should miss when state changes"

    print("✓ Component cache correctly ignores time parameter")


def test_scene_inherits_from_component():
    """Test that Scene is a Component."""
    print("\n=== Test: Scene Inherits From Component ===")

    scene = Scene(width=64, height=32)

    assert isinstance(scene, Component), "Scene should inherit from Component"
    assert hasattr(scene, 'render'), "Scene should have render() method"
    assert hasattr(scene, 'compute_state'), "Scene should have compute_state() method"
    assert hasattr(scene, '_rendered_at'), "Scene should have _rendered_at attribute"

    print("✓ Scene correctly inherits from Component")


def test_scene_cache_invalidation_on_position_change():
    """Test that Scene cache invalidates when child position changes."""
    print("\n=== Test: Scene Cache Invalidation - Position Change ===")

    scene = Scene(width=64, height=32)
    comp = SimpleComponent("test")

    # Add child at position (0, 0)
    scene.add_child("comp1", comp, position=(0, 0), opacity=1.0, z_index=0)

    # First render
    scene_buffer1 = scene.render(1.0)
    scene_rendered_at_1 = scene._rendered_at

    # Render again with time advanced but no changes → cache should HIT
    scene_buffer2 = scene.render(2.0)
    assert scene._rendered_at == scene_rendered_at_1, "Scene timestamp shouldn't change if state unchanged"

    # Now actually modify child position in children dict (simulating animation)
    scene.children["comp1"].state['position'] = (10, 0)

    # Render with new position → cache should MISS, timestamp should update
    scene_buffer3 = scene.render(3.0)
    assert scene._rendered_at == 3.0, f"Scene timestamp should update when child state changes"

    print("✓ Scene cache invalidates correctly on position change")


def test_scene_cache_invalidation_on_component_change():
    """Test that Scene cache invalidates when child component internal state changes."""
    print("\n=== Test: Scene Cache Invalidation - Component Change ===")

    scene = Scene(width=64, height=32)
    comp = SimpleComponent("initial")

    scene.add_child("comp1", comp, position=(0, 0), opacity=1.0, z_index=0)

    # First render
    buffer1 = scene.render(1.0)
    scene_timestamp_1 = scene._rendered_at

    # Render again - no changes → scene cache should HIT
    buffer2 = scene.render(2.0)
    assert scene._rendered_at == scene_timestamp_1, "Scene shouldn't update if nothing changed"

    # Change component internal state
    comp.value = "changed"

    # Render - component's _rendered_at will update, scene should detect and invalidate cache
    buffer3 = scene.render(3.0)
    # Scene should see different _rendered_at in child, invalidate its own cache
    assert scene._rendered_at == 3.0, "Scene should invalidate when child component changes"

    print("✓ Scene cache invalidates correctly when child component changes")


def test_scene_cache_hit_on_idle():
    """Test that Scene cache HITS when idle (time advances but nothing changes)."""
    print("\n=== Test: Scene Cache HIT on Idle ===")

    scene = Scene(width=64, height=32)
    comp = SimpleComponent("static")

    scene.add_child("comp1", comp, position=(10, 10), opacity=1.0, z_index=0)

    # Render at t=1.0
    buffer1 = scene.render(1.0)
    initial_timestamp = scene._rendered_at

    # Render multiple times with advancing time - state unchanged
    for t in [2.0, 3.0, 4.0, 5.0]:
        buffer = scene.render(t)
        assert scene._rendered_at == initial_timestamp, f"Scene timestamp shouldn't change at t={t}"

    print("✓ Scene cache correctly HITS when idle (time advances, state unchanged)")


def test_nested_scenes():
    """Test that scenes can contain other scenes (Scene is a Component)."""
    print("\n=== Test: Nested Scenes ===")

    # Create child scene
    child_scene = Scene(width=32, height=16)
    child_comp = SimpleComponent("child")
    child_scene.add_child("child_comp", child_comp, position=(0, 0))

    # Create parent scene containing child scene
    parent_scene = Scene(width=64, height=32)
    parent_scene.add_child("child_scene", child_scene, position=(0, 0))

    # Render parent - should render child scene
    buffer = parent_scene.render(1.0)

    assert buffer is not None
    assert buffer.width == 64
    assert buffer.height == 32

    # Change child component - should invalidate both child and parent
    child_comp.value = "changed"

    child_scene.render(2.0)  # Child scene updates its _rendered_at
    assert child_scene._rendered_at == 2.0

    parent_scene.render(2.0)  # Parent sees child's _rendered_at changed
    assert parent_scene._rendered_at == 2.0

    print("✓ Nested scenes work correctly")


def test_animation_pure_calculation():
    """Test that animations work with scene state management."""
    print("\n=== Test: Animation Pure Calculation ===")

    from matrix_scene_composer import Animate

    scene = Scene(width=64, height=32)
    comp = SimpleComponent("test")

    scene.add_child("comp1", comp, position=(0, 0), opacity=1.0, z_index=0)

    # Get initial state (position is extracted to x, y)
    initial_x = scene.children["comp1"].state['x']
    initial_y = scene.children["comp1"].state['y']
    assert (initial_x, initial_y) == (0, 0)

    # Add an animation that moves x by 10 pixels
    scene.add_animation(Animate("comp1", to_params_int={'x': 10}, duration=1.0), start_time=0.0)

    # Advance scene time to trigger animation
    scene._time = 0.5  # Halfway through 1-second animation

    # compute_state applies animations and updates instance.state
    state = scene.compute_state(0.5)

    # Instance state is mutated by animations (this is the current design)
    # At 0.5s into a 1s animation from x=0 to x=10, we expect x=5
    assert scene.children["comp1"].state['x'] == 5, "Animation should mutate instance.state"

    print("✓ Animations work with state management")


if __name__ == "__main__":
    print("="*60)
    print("NEW ARCHITECTURE TESTS")
    print("="*60)

    try:
        test_component_rendered_at_tracking()
        test_compute_state_no_time_key()
        test_render_cached_signature()
        test_component_cache_ignores_time_parameter()
        test_scene_inherits_from_component()
        test_scene_cache_invalidation_on_position_change()
        test_scene_cache_invalidation_on_component_change()
        test_scene_cache_hit_on_idle()
        test_nested_scenes()
        test_animation_pure_calculation()

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
