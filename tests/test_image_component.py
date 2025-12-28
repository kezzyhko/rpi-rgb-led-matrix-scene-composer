#!/usr/bin/env python3
"""Test ImageComponent."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import Scene, ImageComponent


def render_to_terminal(buffer):
    """Render buffer to terminal with ANSI true colors."""
    height, width = buffer.height, buffer.width
    for y in range(height):
        for x in range(width):
            r, g, b, a = buffer.get_pixel(x, y)
            # Flatten alpha: fully transparent shows as black
            if a == 0:
                r, g, b = 0, 0, 0
            print(f'\033[38;2;{r};{g};{b}m█\033[0m', end='')
        print()


def test_image_component():
    """Test ImageComponent with test image."""

    print("\n=== Testing ImageComponent ===\n")

    # Path to test image
    test_image = os.path.join(os.path.dirname(__file__), 'resources', '32x24.png')

    # Create image component
    img = ImageComponent(test_image)
    print(f"Image dimensions: {img.width}x{img.height}")

    # Create scene and add image
    scene = Scene(width=img.width, height=img.height)
    scene.add_child('image', img, position=(0, 0))

    # Render and display
    buffer = scene.render(0.0)
    print()
    render_to_terminal(buffer)
    print()

    # Test caching - render again should hit cache
    buffer2 = scene.render(0.0)
    assert buffer.data.tobytes() == buffer2.data.tobytes(), "Cached render should be identical"
    print("✓ Caching working correctly")

    print("\nTest passed!")


if __name__ == '__main__':
    test_image_component()
