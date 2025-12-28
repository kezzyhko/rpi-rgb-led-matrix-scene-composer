"""8px height bitmap font - optimized for LED matrix displays.

This is a 2x pixel-perfect scale of the 4px font, designed for better
readability on small displays. Each pixel from the 4px font becomes a 2x2 block.
"""

import numpy as np

# Helper function to scale 4px glyphs to 8px
def scale_2x(glyph_4px: np.ndarray) -> np.ndarray:
    """Scale a 4px glyph to 8px by doubling each pixel."""
    rows, cols = glyph_4px.shape
    scaled = np.zeros((rows * 2, cols * 2), dtype=np.uint8)

    for r in range(rows):
        for c in range(cols):
            if glyph_4px[r, c]:
                # Each pixel becomes a 2x2 block
                scaled[r*2, c*2] = 1
                scaled[r*2, c*2+1] = 1
                scaled[r*2+1, c*2] = 1
                scaled[r*2+1, c*2+1] = 1

    return scaled


# 8px font - scaled from optimized 4px font
# Import the base 4px font to scale from
from .bitmap_fonts import BITMAP_FONT_4PX

BITMAP_FONT_8PX = {
    char: scale_2x(glyph)
    for char, glyph in BITMAP_FONT_4PX.items()
}
