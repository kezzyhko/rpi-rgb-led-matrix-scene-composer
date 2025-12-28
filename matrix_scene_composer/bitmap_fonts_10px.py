"""10px height bitmap font - optimized for LED matrix displays.

This is a 2x pixel-perfect scale of the 5px font, designed for better
readability on small displays. Each pixel from the 5px font becomes a 2x2 block.
"""

import numpy as np

# Helper function to scale 5px glyphs to 10px
def scale_2x(glyph_5px: np.ndarray) -> np.ndarray:
    """Scale a 5px glyph to 10px by doubling each pixel."""
    rows, cols = glyph_5px.shape
    scaled = np.zeros((rows * 2, cols * 2), dtype=np.uint8)

    for r in range(rows):
        for c in range(cols):
            if glyph_5px[r, c]:
                # Each pixel becomes a 2x2 block
                scaled[r*2, c*2] = 1
                scaled[r*2, c*2+1] = 1
                scaled[r*2+1, c*2] = 1
                scaled[r*2+1, c*2+1] = 1

    return scaled


# 10px font - scaled from optimized 5px font
# Import the base 5px font to scale from
from .bitmap_fonts import BITMAP_FONT_5PX

BITMAP_FONT_10PX = {
    char: scale_2x(glyph)
    for char, glyph in BITMAP_FONT_5PX.items()
}
