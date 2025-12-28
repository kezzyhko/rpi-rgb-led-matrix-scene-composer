"""Optimized bitmap fonts - improvements to readability for low-pixel displays."""

import numpy as np

# Optimized 4px font - fixing problematic characters
OPTIMIZED_4PX_IMPROVEMENTS = {
    # Fix '8' - make it actually look like an 8
    '8': np.array([
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
    ], dtype=np.uint8),

    # Make '8' look more like stacked boxes (alternative)
    '8_alt': np.array([
        [0, 1, 0],
        [1, 1, 1],
        [1, 1, 1],
        [0, 1, 0],
    ], dtype=np.uint8),

    # Fix 'B' - make top distinct
    'B': np.array([
        [1, 1, 0],
        [1, 0, 1],
        [1, 1, 0],
        [1, 0, 1],
    ], dtype=np.uint8),

    # Fix 'N' - make it distinct from H with diagonal
    'N': np.array([
        [1, 0, 1],
        [1, 1, 1],
        [1, 1, 1],
        [1, 0, 1],
    ], dtype=np.uint8),

    # Better 'N' with visible diagonal
    'N_alt': np.array([
        [1, 0, 0, 1],
        [1, 1, 0, 1],
        [1, 0, 1, 1],
        [1, 0, 0, 1],
    ], dtype=np.uint8),

    # Fix 'V' - make it different from U
    'V': np.array([
        [1, 0, 1],
        [1, 0, 1],
        [0, 1, 0],
        [0, 1, 0],
    ], dtype=np.uint8),

    # Add '-' (hyphen/dash) - CRITICAL for flight display
    '-': np.array([
        [0, 0],
        [1, 1],
        [0, 0],
        [0, 0],
    ], dtype=np.uint8),

    # Add '>' (greater than) - CRITICAL for "JFK>LHR" display
    '>': np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [0, 1, 0],
    ], dtype=np.uint8),

    # Alternative '>' more arrow-like
    '>_arrow': np.array([
        [1, 0],
        [0, 1],
        [1, 0],
        [0, 0],
    ], dtype=np.uint8),

    # Add '/' (slash)
    '/': np.array([
        [0, 0, 1],
        [0, 0, 1],
        [0, 1, 0],
        [1, 0, 0],
    ], dtype=np.uint8),

    # Add ',' (comma)
    ',': np.array([
        [0],
        [0],
        [1],
        [1],
    ], dtype=np.uint8),

    # Improve '1' - make it more distinct
    '1': np.array([
        [1, 1],
        [0, 1],
        [0, 1],
        [1, 1, 1],
    ], dtype=np.uint8),

    # Improve '3' - clearer curves
    '3': np.array([
        [1, 1, 1],
        [0, 1, 1],
        [0, 0, 1],
        [1, 1, 1],
    ], dtype=np.uint8),

    # Improve '6' - more distinct
    '6': np.array([
        [0, 1, 1],
        [1, 0, 0],
        [1, 1, 1],
        [0, 1, 0],
    ], dtype=np.uint8),

    # Improve '9' - mirror of 6
    '9': np.array([
        [0, 1, 0],
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 0],
    ], dtype=np.uint8),
}

# Optimized 5px font improvements
OPTIMIZED_5PX_IMPROVEMENTS = {
    # Better '8'
    '8': np.array([
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [0, 1, 1, 0],
    ], dtype=np.uint8),

    # Add '-' (hyphen/dash)
    '-': np.array([
        [0, 0, 0],
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
        [0, 0, 0],
    ], dtype=np.uint8),

    # Add '>' (greater than)
    '>': np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.uint8),

    # Alternative '>' more compact
    '>_compact': np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [0, 1, 0],
        [1, 0, 0],
    ], dtype=np.uint8),

    # Add '/' (slash)
    '/': np.array([
        [0, 0, 0, 1],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.uint8),

    # Add ',' (comma)
    ',': np.array([
        [0],
        [0],
        [0],
        [1],
        [1],
    ], dtype=np.uint8),

    # Better 'V' that actually tapers
    'V': np.array([
        [1, 0, 0, 1],
        [1, 0, 0, 1],
        [1, 0, 0, 1],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
    ], dtype=np.uint8),
}


# Analysis notes for reference
"""
CRITICAL MISSING CHARACTERS for flight tracker:
- '-' (dash) - essential for separators
- '>' (greater than) - currently using but NOT DEFINED in font!

PROBLEMATIC 4PX CHARACTERS TO FIX:
1. '8' - diamond shape instead of stacked circles
2. 'B' - top half malformed
3. 'N' - identical to 'H'
4. 'U' & 'V' - identical glyphs
5. '3', '6', '9' - unclear curves

PROBLEMATIC 5PX CHARACTERS:
1. '8' - still unclear stacking
2. 'V' - tapers incorrectly

OPTIMAL DESIGN PRINCIPLES FOR LOW-PIXEL FONTS:
1. Maximize filled pixels while maintaining shape
2. Use full width available (3px for most, 4-5px for wider chars)
3. Ensure diagonal strokes are visible
4. Make similar chars distinctly different (B/8, O/0, I/1)
5. Prefer blocky over curvy for clarity
6. Use symmetry where appropriate (8, 0, X)
7. Keep counters (interior spaces) open and clear
"""
