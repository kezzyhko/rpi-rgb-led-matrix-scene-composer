#!/usr/bin/env python3
"""Test Text4pxComponent and Text5pxComponent."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import Orchestrator, Scene, Text4pxComponent, Text5pxComponent


def render_to_terminal(buffer):
    """Render buffer to terminal with ANSI true colors."""
    height, width = buffer.height, buffer.width
    for y in range(height):
        for x in range(width):
            r, g, b = buffer.get_pixel(x, y)
            print(f'\033[38;2;{r};{g};{b}m█\033[0m', end='')
        print()


def test_text_components():
    """Test both 4px and 5px text components."""

    print("\n=== Testing Text4pxComponent (4px height) ===\n")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Test 4px component
    text1 = Text4pxComponent(scene, text="HELLO WORLD", fgcolor=(255, 0, 0))
    print(f"Text4px 'HELLO WORLD' dimensions: {text1.width}x{text1.height}")
    scene.add_component('text1', text1, position=(2, 2))

    text2 = Text4pxComponent(scene, text="ULTRA COMPACT", fgcolor=(0, 255, 0))
    print(f"Text4px 'ULTRA COMPACT' dimensions: {text2.width}x{text2.height}")
    scene.add_component('text2', text2, position=(2, 8))

    text3 = Text4pxComponent(scene, text="4PX HEIGHT!", fgcolor=(0, 255, 255))
    print(f"Text4px '4PX HEIGHT!' dimensions: {text3.width}x{text3.height}")
    scene.add_component('text3', text3, position=(2, 14))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    buffer = orch.render_single_frame(0.0)
    print()
    render_to_terminal(buffer)

    print("\n\n=== Testing Text5pxComponent (5px height) ===\n")

    orch2 = Orchestrator(width=width, height=height, fps=10)
    scene2 = Scene(orch2, width=width, height=height)

    # Test 5px component
    text4 = Text5pxComponent(scene2, text="HELLO WORLD", fgcolor=(255, 0, 0))
    print(f"Text5px 'HELLO WORLD' dimensions: {text4.width}x{text4.height}")
    scene2.add_component('text4', text4, position=(2, 2))

    text5 = Text5pxComponent(scene2, text="MORE READABLE", fgcolor=(0, 255, 0))
    print(f"Text5px 'MORE READABLE' dimensions: {text5.width}x{text5.height}")
    scene2.add_component('text5', text5, position=(2, 9))

    text6 = Text5pxComponent(scene2, text="5PX HEIGHT!", fgcolor=(255, 255, 0))
    print(f"Text5px '5PX HEIGHT!' dimensions: {text6.width}x{text6.height}")
    scene2.add_component('text6', text6, position=(2, 16))

    orch2.add_scene('test2', scene2)
    orch2.transition_to('test2')

    buffer2 = orch2.render_single_frame(0.0)
    print()
    render_to_terminal(buffer2)

    print("\n\n=== Testing bgcolor and padding ===\n")

    orch3 = Orchestrator(width=width, height=height, fps=10)
    scene3 = Scene(orch3, width=width, height=height)

    # Test with background colors and padding
    text7 = Text4pxComponent(scene3, text="BG COLOR", fgcolor=(255, 255, 0), bgcolor=(0, 0, 128), padding=2)
    print(f"Text4px with bgcolor and padding=2: {text7.width}x{text7.height}")
    scene3.add_component('text7', text7, position=(2, 2))

    text8 = Text5pxComponent(scene3, text="PADDED", fgcolor=(0, 0, 0), bgcolor=(255, 100, 0), padding=3)
    print(f"Text5px with bgcolor and padding=3: {text8.width}x{text8.height}")
    scene3.add_component('text8', text8, position=(2, 10))

    orch3.add_scene('test3', scene3)
    orch3.transition_to('test3')

    buffer3 = orch3.render_single_frame(0.0)
    print()
    render_to_terminal(buffer3)

    print("\n\n=== Comparison ===")
    print("Text4px: 4 pixels high - ultra compact")
    print("Text5px: 5 pixels high - more readable")
    print("Both support fgcolor, bgcolor, and padding")
    print()


if __name__ == "__main__":
    test_text_components()
