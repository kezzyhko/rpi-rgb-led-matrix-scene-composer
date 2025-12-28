#!/usr/bin/env python3
"""Test ultra-compact 4px height bitmap font."""

import numpy as np

# Define each letter as 4px height x variable width
# 1 = pixel on, 0 = pixel off
# Each letter is designed to be as narrow as possible while remaining readable

BITMAP_FONT_4PX = {
    'A': np.array([
        [0, 1, 0],
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
    ], dtype=np.uint8),

    'B': np.array([
        [1, 1, 0],
        [1, 1, 0],
        [1, 0, 1],
        [1, 1, 0],
    ], dtype=np.uint8),

    'C': np.array([
        [0, 1, 1],
        [1, 0, 0],
        [1, 0, 0],
        [0, 1, 1],
    ], dtype=np.uint8),

    'D': np.array([
        [1, 1, 0],
        [1, 0, 1],
        [1, 0, 1],
        [1, 1, 0],
    ], dtype=np.uint8),

    'E': np.array([
        [1, 1, 1],
        [1, 1, 0],
        [1, 0, 0],
        [1, 1, 1],
    ], dtype=np.uint8),

    'F': np.array([
        [1, 1, 1],
        [1, 1, 0],
        [1, 0, 0],
        [1, 0, 0],
    ], dtype=np.uint8),

    'G': np.array([
        [0, 1, 1],
        [1, 0, 0],
        [1, 0, 1],
        [0, 1, 1],
    ], dtype=np.uint8),

    'H': np.array([
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
        [1, 0, 1],
    ], dtype=np.uint8),

    'I': np.array([
        [1],
        [1],
        [1],
        [1],
    ], dtype=np.uint8),

    'J': np.array([
        [0, 1],
        [0, 1],
        [1, 1],
        [0, 1],
    ], dtype=np.uint8),

    'K': np.array([
        [1, 0, 1],
        [1, 1, 0],
        [1, 0, 0],
        [1, 0, 1],
    ], dtype=np.uint8),

    'L': np.array([
        [1, 0],
        [1, 0],
        [1, 0],
        [1, 1],
    ], dtype=np.uint8),

    'M': np.array([
        [1, 0, 0, 0, 1],
        [1, 1, 0, 1, 1],
        [1, 0, 1, 0, 1],
        [1, 0, 0, 0, 1],
    ], dtype=np.uint8),

    'N': np.array([
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
        [1, 0, 1],
    ], dtype=np.uint8),

    'O': np.array([
        [0, 1, 0],
        [1, 0, 1],
        [1, 0, 1],
        [0, 1, 0],
    ], dtype=np.uint8),

    'P': np.array([
        [1, 1, 0],
        [1, 0, 1],
        [1, 1, 0],
        [1, 0, 0],
    ], dtype=np.uint8),

    'Q': np.array([
        [0, 1, 0],
        [1, 0, 1],
        [1, 0, 1],
        [0, 1, 1],
    ], dtype=np.uint8),

    'R': np.array([
        [1, 1, 0],
        [1, 0, 1],
        [1, 1, 0],
        [1, 0, 1],
    ], dtype=np.uint8),

    'S': np.array([
        [0, 1, 1],
        [1, 1, 0],
        [0, 0, 1],
        [1, 1, 0],
    ], dtype=np.uint8),

    'T': np.array([
        [1, 1, 1],
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ], dtype=np.uint8),

    'U': np.array([
        [1, 0, 1],
        [1, 0, 1],
        [1, 0, 1],
        [0, 1, 0],
    ], dtype=np.uint8),

    'V': np.array([
        [1, 0, 1],
        [1, 0, 1],
        [1, 0, 1],
        [0, 1, 0],
    ], dtype=np.uint8),

    'W': np.array([
        [1, 0, 0, 0, 1],
        [1, 0, 1, 0, 1],
        [1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0],
    ], dtype=np.uint8),

    'X': np.array([
        [1, 0, 1],
        [0, 1, 0],
        [0, 1, 0],
        [1, 0, 1],
    ], dtype=np.uint8),

    'Y': np.array([
        [1, 0, 1],
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ], dtype=np.uint8),

    'Z': np.array([
        [1, 1, 1],
        [0, 0, 1],
        [0, 1, 0],
        [1, 1, 1],
    ], dtype=np.uint8),

    ' ': np.array([
        [0],
        [0],
        [0],
        [0],
    ], dtype=np.uint8),
}


def render_text_to_array(text):
    """Render text using 4px bitmap font, returns numpy array."""
    text = text.upper()

    # Calculate total width needed
    letter_arrays = []
    for char in text:
        if char in BITMAP_FONT_4PX:
            letter_arrays.append(BITMAP_FONT_4PX[char])
        else:
            # Unknown character, use space
            letter_arrays.append(BITMAP_FONT_4PX[' '])

    # Add 1px spacing between letters
    spaced_arrays = []
    for i, letter in enumerate(letter_arrays):
        spaced_arrays.append(letter)
        if i < len(letter_arrays) - 1:  # Don't add space after last letter
            # 1px spacing column
            spacing = np.zeros((4, 1), dtype=np.uint8)
            spaced_arrays.append(spacing)

    # Concatenate horizontally
    result = np.hstack(spaced_arrays)
    return result


def visualize_array(array):
    """Print array as ASCII art."""
    for row in array:
        line = ''
        for pixel in row:
            line += '█' if pixel else ' '
        print(line)


if __name__ == "__main__":
    print("4px Height Bitmap Font - Full Alphabet")
    print("=" * 60)
    print()

    # Show alphabet
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    print("Full alphabet:")
    alphabet_array = render_text_to_array(alphabet)
    visualize_array(alphabet_array)
    print(f"Width: {alphabet_array.shape[1]} pixels, Height: {alphabet_array.shape[0]} pixels")
    print()

    # Show test message
    print("\nTest message:")
    test_array = render_text_to_array("HELLO WORLD")
    visualize_array(test_array)
    print(f"Width: {test_array.shape[1]} pixels, Height: {test_array.shape[0]} pixels")
    print()

    # Show another test
    print("\nCompact test:")
    test_array2 = render_text_to_array("ULTRA COMPACT")
    visualize_array(test_array2)
    print(f"Width: {test_array2.shape[1]} pixels, Height: {test_array2.shape[0]} pixels")
