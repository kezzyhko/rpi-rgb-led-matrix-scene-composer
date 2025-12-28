#!/usr/bin/env python3
"""Test unified TextComponent for all font heights (4-16px)."""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import Orchestrator, Scene, TextComponent


def render_to_terminal(buffer):
    """Render buffer to terminal with ANSI true colors."""
    height, width = buffer.height, buffer.width
    for y in range(height):
        for x in range(width):
            r, g, b, a = buffer.get_pixel(x, y)
            print(f'\033[38;2;{r};{g};{b}m█\033[0m', end='')
        print()


def test_specific_size(font_height):
    """Test a specific font height."""

    print(f"\n=== Testing TextComponent(font_height={font_height}) ===\n")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(width=width, height=height)

    # Test basic text
    text1 = TextComponent(text="HELLO WORLD", font_height=font_height, fgcolor=(255, 0, 0))
    print(f"TextComponent(font_height={font_height}) 'HELLO WORLD' dimensions: {text1.width}x{text1.height}")
    y_pos = 2
    scene.add_child('text1', text1, position=(2, y_pos))

    y_pos += font_height + 2
    text2 = TextComponent(text="ABCDEFGHIJKLM", font_height=font_height, fgcolor=(0, 255, 0))
    print(f"TextComponent(font_height={font_height}) 'ABCDEFGHIJKLM' dimensions: {text2.width}x{text2.height}")
    scene.add_child('text2', text2, position=(2, y_pos))

    y_pos += font_height + 2
    text3 = TextComponent(text="0123456789", font_height=font_height, fgcolor=(0, 255, 255))
    print(f"TextComponent(font_height={font_height}) '0123456789' dimensions: {text3.width}x{text3.height}")
    scene.add_child('text3', text3, position=(2, y_pos))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    buffer = orch.render_single_frame(0.0)
    print()
    render_to_terminal(buffer)

    print(f"\n\n=== Testing bgcolor and padding (font_height={font_height}) ===\n")

    orch2 = Orchestrator(width=width, height=height, fps=10)
    scene2 = Scene(width=width, height=height)

    # Test with background colors and padding
    text4 = TextComponent(text="BG COLOR", font_height=font_height, fgcolor=(255, 255, 0), bgcolor=(0, 0, 128), padding=2)
    print(f"TextComponent(font_height={font_height}) with bgcolor and padding=2: {text4.width}x{text4.height}")
    scene2.add_child('text4', text4, position=(2, 2))

    text5 = TextComponent(text="PADDED", font_height=font_height, fgcolor=(0, 0, 0), bgcolor=(255, 100, 0), padding=3)
    print(f"TextComponent(font_height={font_height}) with bgcolor and padding=3: {text5.width}x{text5.height}")
    scene2.add_child('text5', text5, position=(2, 2 + font_height + 6))

    orch2.add_scene('test2', scene2)
    orch2.transition_to('test2')

    buffer2 = orch2.render_single_frame(0.0)
    print()
    render_to_terminal(buffer2)

    print(f"\n\n=== TextComponent(font_height={font_height}) Test Complete ===")
    print(f"Font height: {font_height} pixels")
    print(f"Letter spacing: {1 if font_height < 8 else 2}px")
    print("Supports fgcolor, bgcolor, and padding")
    print()


def test_all_sizes():
    """Test all available font heights (4-16px)."""
    for font_height in range(4, 17):
        test_specific_size(font_height)
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test TextComponent for LED matrix')
    parser.add_argument('font_height', type=int, nargs='?', default=None,
                        help='Font height to test (4-16). If not specified, tests all.')
    args = parser.parse_args()

    if args.font_height is not None:
        if args.font_height < 4 or args.font_height > 16:
            print(f"Error: Font height must be between 4 and 16. Got: {args.font_height}")
            sys.exit(1)
        test_specific_size(args.font_height)
    else:
        test_all_sizes()
