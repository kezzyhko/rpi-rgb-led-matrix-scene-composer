#!/usr/bin/env python3
"""Test core component caching functionality.

Tests the @cache_with_dict decorator and Component.compute_state() pattern.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import Component, RenderBuffer, cache_with_dict


class SimpleComponent(Component):
    """Minimal component for testing caching."""

    def __init__(self, scene, value: str):
        super().__init__(scene)
        self.value = value
        self.render_count = 0

    @property
    def width(self) -> int:
        return 10

    @property
    def height(self) -> int:
        return 10

    def compute_state(self, time: float) -> dict:
        """State depends on value and time."""
        return {
            'value': self.value,
            'time': int(time)  # Quantize time to test caching
        }

    def render(self, time: float) -> RenderBuffer:
        """Render using cached rendering."""
        state = self.compute_state(time)
        return self._render_cached(state)

    @cache_with_dict(maxsize=128)
    def _render_cached(self, state) -> RenderBuffer:
        """This should only be called on cache misses."""
        self.render_count += 1
        buffer = RenderBuffer(self.width, self.height)
        # Just fill with white to show it rendered
        for y in range(self.height):
            for x in range(self.width):
                buffer.set_pixel(x, y, (255, 255, 255))
        return buffer


def test_cache_hit():
    """Test that same state uses cache (doesn't re-render)."""
    print("\n=== Test: Cache Hit ===")

    # Create a mock scene
    class MockScene:
        time = 0.0

    scene = MockScene()
    comp = SimpleComponent(scene, "test")

    # First render - should be cache miss
    buffer1 = comp.render(0.0)
    assert comp.render_count == 1, "First render should execute"

    # Second render with same time - should be cache hit
    buffer2 = comp.render(0.0)
    assert comp.render_count == 1, "Second render with same state should use cache"

    # Verify buffers are identical (same object)
    assert buffer1 is buffer2, "Cached buffer should be same object"

    print(f"✓ Render count: {comp.render_count} (expected 1)")
    print("✓ Cache hit successful - no re-render occurred")


def test_cache_miss():
    """Test that different state causes cache miss (re-render)."""
    print("\n=== Test: Cache Miss ===")

    class MockScene:
        time = 0.0

    scene = MockScene()
    comp = SimpleComponent(scene, "test")

    # First render at time 0
    buffer1 = comp.render(0.0)
    assert comp.render_count == 1

    # Second render at time 1 - different state
    buffer2 = comp.render(1.0)
    assert comp.render_count == 2, "Different state should cause re-render"

    # Third render back at time 0 - should hit cache from first render
    buffer3 = comp.render(0.0)
    assert comp.render_count == 2, "Should use cached result from first render"

    # Verify buffer3 is same as buffer1 (cached)
    assert buffer3 is buffer1, "Cache should return original buffer"

    print(f"✓ Render count: {comp.render_count} (expected 2)")
    print("✓ Cache miss correctly triggered re-render")
    print("✓ Cache correctly reused old result")


def test_state_quantization():
    """Test that compute_state() controls cache granularity."""
    print("\n=== Test: State Quantization ===")

    class MockScene:
        time = 0.0

    scene = MockScene()
    comp = SimpleComponent(scene, "test")

    # Render at time 0.1 and 0.9 - both quantize to int(0)
    buffer1 = comp.render(0.1)
    assert comp.render_count == 1

    buffer2 = comp.render(0.9)
    assert comp.render_count == 1, "0.1 and 0.9 both quantize to 0, should use cache"

    # Render at time 1.1 - quantizes to int(1)
    buffer3 = comp.render(1.1)
    assert comp.render_count == 2, "1.1 quantizes to 1, different state"

    print(f"✓ Render count: {comp.render_count} (expected 2)")
    print("✓ State quantization correctly controls cache behavior")


def test_multiple_instances():
    """Test that different instances have separate caches."""
    print("\n=== Test: Multiple Instances ===")

    class MockScene:
        time = 0.0

    scene = MockScene()
    comp1 = SimpleComponent(scene, "first")
    comp2 = SimpleComponent(scene, "second")

    # Render both at same time
    buffer1 = comp1.render(0.0)
    buffer2 = comp2.render(0.0)

    # Each should render once (different instances)
    assert comp1.render_count == 1, "First instance should render"
    assert comp2.render_count == 1, "Second instance should render"

    # Re-render both - should use cache
    buffer1_cached = comp1.render(0.0)
    buffer2_cached = comp2.render(0.0)

    assert comp1.render_count == 1, "First instance should use cache"
    assert comp2.render_count == 1, "Second instance should use cache"

    # Verify buffers are cached
    assert buffer1 is buffer1_cached
    assert buffer2 is buffer2_cached

    print("✓ Each instance maintains separate cache")
    print("✓ Cache works correctly across multiple instances")


if __name__ == "__main__":
    test_cache_hit()
    test_cache_miss()
    test_state_quantization()
    test_multiple_instances()

    print("\n" + "="*50)
    print("COMPONENT CACHING TESTS PASSED")
    print("="*50)
    print("✓ @cache_with_dict decorator works correctly")
    print("✓ compute_state() controls cache behavior")
    print("✓ Cache hits/misses work as expected")
    print()
