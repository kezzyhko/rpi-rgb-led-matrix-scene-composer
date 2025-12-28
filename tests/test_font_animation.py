#!/usr/bin/env python3
"""Animated character viewer for reviewing font designs.

Usage:
    python tests/test_font_animation.py 4   # View 4px font
    python tests/test_font_animation.py 5   # View 5px font
    python tests/test_font_animation.py 8   # View 8px font
    python tests/test_font_animation.py 10  # View 10px font
"""

import sys
import time
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from matrix_scene_composer.text_component import (
    TextComponent
)
from matrix_scene_composer.font_library import BITMAP_FONT_4PX, BITMAP_FONT_5PX
from matrix_scene_composer.bitmap_fonts_8px import BITMAP_FONT_8PX
from matrix_scene_composer.bitmap_fonts_10px import BITMAP_FONT_10PX


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def visualize_buffer(buffer, scale=1):
    """
    Visualize a RenderBuffer as ASCII art in the terminal.

    Args:
        buffer: RenderBuffer instance
        scale: Integer scaling factor (1 = normal, 2 = 2x size, etc.)
    """
    lines = []
    for y in range(buffer.height):
        line = ''
        for x in range(buffer.width):
            r, g, b, a = buffer.get_pixel(x, y)
            # Simple thresholding: if any color component > 128, show as filled
            if r > 128 or g > 128 or b > 128:
                char = '█'
            else:
                char = ' '

            # Apply horizontal scaling
            line += char * scale

        # Apply vertical scaling by repeating lines
        for _ in range(scale):
            lines.append(line)

    return '\n'.join(lines)


def get_character_name(char):
    """Get human-readable name for a character."""
    names = {
        ' ': 'SPACE',
        '!': 'EXCLAMATION',
        '.': 'PERIOD',
        ':': 'COLON',
        '-': 'HYPHEN/MINUS',
        '>': 'GREATER THAN',
        '→': 'RIGHT ARROW',
    }

    if char in names:
        return names[char]
    elif char.isalpha():
        return f"LETTER {char}"
    elif char.isdigit():
        return f"DIGIT {char}"
    else:
        return f"CHAR '{char}'"


def animate_font(font_size):
    """
    Animate through all characters in the specified font size.

    Args:
        font_size: Integer (4, 5, 8, or 10)
    """
    # Select appropriate component and font dictionary
    if font_size == 4:
        ComponentClass = TextComponent
        font_dict = BITMAP_FONT_4PX
        scale = 3  # Scale up for better visibility
    elif font_size == 5:
        ComponentClass = TextComponent
        font_dict = BITMAP_FONT_5PX
        scale = 3
    elif font_size == 8:
        ComponentClass = TextComponent
        font_dict = BITMAP_FONT_8PX
        scale = 2
    elif font_size == 10:
        ComponentClass = TextComponent
        font_dict = BITMAP_FONT_10PX
        scale = 2
    else:
        print(f"Error: Unsupported font size {font_size}")
        print("Supported sizes: 4, 5, 8, 10")
        sys.exit(1)

    # Get all characters in order: A-Z, 0-9, then specials
    chars = sorted(font_dict.keys(), key=lambda c: (
        0 if c.isalpha() else 1 if c.isdigit() else 2,  # Sort order
        c  # Then alphabetically/numerically
    ))

    print(f"Font {font_size}px Character Viewer")
    print(f"Total characters: {len(chars)}")
    print("=" * 60)
    print("\nStarting animation in 2 seconds...")
    print("(Press Ctrl+C to exit)")
    time.sleep(2)

    frame_delay = 0.5  # seconds between characters

    try:
        for i, char in enumerate(chars):
            clear_screen()

            # Create component with this character
            component = ComponentClass(
                text=char,
                fgcolor=(255, 255, 255),
                bgcolor=None,
                padding=2
            )

            # Render at time=0 (static text doesn't change with time)
            buffer = component.render(time=0.0)

            # Display header
            print(f"Font: {font_size}px | Character {i+1}/{len(chars)}")
            print("=" * 60)
            print(f"\n{get_character_name(char)}: '{char}'")
            print(f"Dimensions: {buffer.width}x{buffer.height} pixels")
            print(f"Character width: {font_dict[char].shape[1]}px (excluding padding)")
            print()

            # Display the character (scaled up for visibility)
            print(visualize_buffer(buffer, scale=scale))
            print()

            # Progress indicator
            progress = "█" * (i + 1) + "░" * (len(chars) - i - 1)
            print(f"\nProgress: [{progress}] {i+1}/{len(chars)}")

            time.sleep(frame_delay)

        # Final summary
        clear_screen()
        print(f"✓ Font {font_size}px Review Complete!")
        print("=" * 60)
        print(f"Reviewed {len(chars)} characters")
        print(f"\nCharacter set: {' '.join(chars)}")
        print()

    except KeyboardInterrupt:
        print("\n\nAnimation interrupted by user.")
        sys.exit(0)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        print("\nError: Font size argument required")
        print("Supported sizes: 4, 5, 8, 10")
        sys.exit(1)

    try:
        font_size = int(sys.argv[1])
    except ValueError:
        print(f"Error: Invalid font size '{sys.argv[1]}' (must be an integer)")
        sys.exit(1)

    animate_font(font_size)


if __name__ == "__main__":
    main()
