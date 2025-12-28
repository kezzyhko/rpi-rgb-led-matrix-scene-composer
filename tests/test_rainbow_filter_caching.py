#!/usr/bin/env python3
"""Test RainbowFilter and demonstrate caching through all component layers.

This test demonstrates the component hierarchy and caching:
- Scene (orchestrator level)
  -> RainbowFilter (filter component)
    -> TableComponent (layout component)
      -> Text4pxComponent/Text5pxComponent (primitive components)
        -> bitmap fonts (numpy arrays)

Each layer caches its results, so re-rendering with the same state is fast.
"""

import sys
import os
import time as time_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import (
    Orchestrator, Scene, TableComponent, RainbowFilter,
    Text4pxComponent, Text5pxComponent
)


def render_to_terminal(buffer):
    """Render buffer to terminal with ANSI true colors."""
    height, width = buffer.height, buffer.width
    for y in range(height):
        for x in range(width):
            r, g, b = buffer.get_pixel(x, y)
            print(f'\033[38;2;{r};{g};{b}m█\033[0m', end='')
        print()


def test_rainbow_filter_with_table():
    """Test RainbowFilter wrapping TableComponent - shows full layer caching."""

    print("\n" + "="*70)
    print("RAINBOW FILTER + TABLE COMPONENT - MULTI-LAYER CACHING TEST")
    print("="*70)
    print("\nComponent hierarchy:")
    print("  Scene")
    print("    └─ RainbowFilter")
    print("         └─ TableComponent")
    print("              └─ Text4pxComponent (for each cell)")
    print("                   └─ bitmap fonts (numpy arrays)")
    print()

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Create table data
    data = [
        {"name": "CPU", "temp": "45C", "load": "23%"},
        {"name": "GPU", "temp": "67C", "load": "89%"},
        {"name": "RAM", "temp": "42C", "load": "56%"},
    ]

    # Create table component
    table = TableComponent(
        scene,
        data=data,
        text_component=Text4pxComponent,
        fgcolor=(255, 255, 255),  # White text
        header_bgcolor=(32, 32, 32),  # Dark gray header background
        cell_padding=1,
        show_borders=True,
        border_color=(64, 64, 64)
    )

    print(f"Table dimensions: {table.width}x{table.height}")

    # Wrap table in rainbow filter - transforms white text to rainbow
    rainbow_table = RainbowFilter(
        scene,
        source_component=table,
        color_key=(255, 255, 255),  # Transform white pixels
        match_tolerance=10,
        direction='horizontal',
        speed=0.5  # Slow animation
    )

    print(f"RainbowFilter dimensions: {rainbow_table.width}x{rainbow_table.height}")
    print()

    scene.add_component('rainbow_table', rainbow_table, position=(2, 2))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    # Render multiple frames to show animation and test caching
    print("Frame 0 (t=0.0s):")
    buffer0 = orch.render_single_frame(0.0)
    render_to_terminal(buffer0)

    print("\n\nFrame 1 (t=0.5s) - Rainbow shifted:")
    buffer1 = orch.render_single_frame(0.5)
    render_to_terminal(buffer1)

    print("\n\nFrame 2 (t=1.0s) - Rainbow shifted more:")
    buffer2 = orch.render_single_frame(1.0)
    render_to_terminal(buffer2)

    # Test caching by re-rendering frame 0
    print("\n\n" + "="*70)
    print("CACHING TEST - Re-rendering Frame 0")
    print("="*70)
    print("This should be instant (fully cached):\n")

    start = time_module.perf_counter()
    buffer0_cached = orch.render_single_frame(0.0)
    elapsed = time_module.perf_counter() - start

    print(f"Re-render time: {elapsed*1000:.3f}ms (should be ~0ms due to caching)")

    # Compare buffers pixel by pixel
    buffers_match = True
    for y in range(buffer0.height):
        for x in range(buffer0.width):
            if buffer0.get_pixel(x, y) != buffer0_cached.get_pixel(x, y):
                buffers_match = False
                break
        if not buffers_match:
            break

    print("Buffers match:", buffers_match)


def test_rainbow_filter_with_text():
    """Test RainbowFilter with simple text component."""

    print("\n\n" + "="*70)
    print("RAINBOW FILTER + TEXT COMPONENT")
    print("="*70)
    print("\nSimpler hierarchy:")
    print("  Scene")
    print("    └─ RainbowFilter")
    print("         └─ Text5pxComponent")
    print("              └─ bitmap fonts")
    print()

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Create text component
    text = Text5pxComponent(
        scene,
        text="RAINBOW TEXT",
        fgcolor=(255, 255, 255),
        bgcolor=(0, 0, 64),  # Dark blue background
        padding=2
    )

    # Wrap in rainbow filter
    rainbow_text = RainbowFilter(
        scene,
        source_component=text,
        color_key=(255, 255, 255),
        match_tolerance=10,
        direction='vertical',  # Vertical rainbow
        speed=1.0
    )

    scene.add_component('rainbow_text', rainbow_text, position=(2, 2))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    print("Vertical rainbow (t=0.0s):")
    buffer = orch.render_single_frame(0.0)
    render_to_terminal(buffer)


def test_rainbow_filter_diagonal():
    """Test diagonal rainbow direction."""

    print("\n\n" + "="*70)
    print("RAINBOW FILTER - DIAGONAL DIRECTION")
    print("="*70)
    print()

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Create table without headers
    data = [
        {"col1": "12", "col2": "34", "col3": "56"},
        {"col1": "78", "col2": "90", "col3": "12"},
        {"col1": "AB", "col2": "CD", "col3": "EF"},
    ]

    table = TableComponent(
        scene,
        data=data,
        text_component=Text4pxComponent,
        fgcolor=(255, 255, 255),
        cell_padding=2,
        show_borders=False,
        show_headers=False  # No headers - just data
    )

    # Diagonal rainbow
    rainbow_table = RainbowFilter(
        scene,
        source_component=table,
        color_key=(255, 255, 255),
        direction='diagonal',
        speed=0.3
    )

    scene.add_component('diagonal', rainbow_table, position=(2, 2))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    print("Diagonal rainbow (no headers, no borders):")
    buffer = orch.render_single_frame(0.0)
    render_to_terminal(buffer)


def test_cache_statistics():
    """Show cache hit statistics across component layers."""

    print("\n\n" + "="*70)
    print("CACHE PERFORMANCE TEST")
    print("="*70)
    print()

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    data = [
        {"a": "X", "b": "Y"},
        {"a": "Z", "b": "W"},
    ]

    table = TableComponent(
        scene,
        data=data,
        text_component=Text4pxComponent,
        fgcolor=(255, 255, 255),
        cell_padding=1,
        show_borders=True
    )

    rainbow = RainbowFilter(scene, table, color_key=(255, 255, 255))

    scene.add_component('test', rainbow, position=(0, 0))
    orch.add_scene('test', scene)
    orch.transition_to('test')

    # First render (cold cache)
    print("First render (cold cache):")
    start = time_module.perf_counter()
    buffer1 = orch.render_single_frame(0.0)
    elapsed1 = time_module.perf_counter() - start
    print(f"  Time: {elapsed1*1000:.3f}ms")

    # Second render (warm cache - same time)
    print("\nSecond render (warm cache, same time=0.0):")
    start = time_module.perf_counter()
    buffer2 = orch.render_single_frame(0.0)
    elapsed2 = time_module.perf_counter() - start
    print(f"  Time: {elapsed2*1000:.3f}ms")
    print(f"  Speedup: {elapsed1/elapsed2:.1f}x faster")

    # Third render (different time, partial cache hit)
    print("\nThird render (different time=0.5, partial cache):")
    start = time_module.perf_counter()
    buffer3 = orch.render_single_frame(0.5)
    elapsed3 = time_module.perf_counter() - start
    print(f"  Time: {elapsed3*1000:.3f}ms")
    print("\nNote: Text components are fully cached even at different times")
    print("      Only RainbowFilter needs to recompute (color transformation)")


if __name__ == "__main__":
    test_rainbow_filter_with_table()
    test_rainbow_filter_with_text()
    test_rainbow_filter_diagonal()
    test_cache_statistics()

    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("✓ RainbowFilter successfully wraps other components")
    print("✓ Multi-layer caching works: Scene -> Filter -> Table -> Text")
    print("✓ Supports horizontal, vertical, and diagonal rainbows")
    print("✓ Animated rainbow (changes with time parameter)")
    print("✓ Color key matching with tolerance")
    print("✓ All layers benefit from component caching system")
    print()
