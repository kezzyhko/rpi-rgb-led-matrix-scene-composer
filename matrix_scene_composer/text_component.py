"""Ultra-compact bitmap text component for LED matrix displays."""

import numpy as np
from typing import Tuple
from .component import Component, cache_with_dict
from .render_buffer import RenderBuffer
from .font_library import (
    BITMAP_FONT_4PX, BITMAP_FONT_5PX, BITMAP_FONT_6PX,
    BITMAP_FONT_7PX, BITMAP_FONT_8PX, BITMAP_FONT_9PX,
    BITMAP_FONT_10PX, BITMAP_FONT_11PX, BITMAP_FONT_12PX,
    BITMAP_FONT_13PX, BITMAP_FONT_14PX, BITMAP_FONT_15PX,
    BITMAP_FONT_16PX
)

# Font mapping for all available sizes
FONT_MAP = {
    4: BITMAP_FONT_4PX,
    5: BITMAP_FONT_5PX,
    6: BITMAP_FONT_6PX,
    7: BITMAP_FONT_7PX,
    8: BITMAP_FONT_8PX,
    9: BITMAP_FONT_9PX,
    10: BITMAP_FONT_10PX,
    11: BITMAP_FONT_11PX,
    12: BITMAP_FONT_12PX,
    13: BITMAP_FONT_13PX,
    14: BITMAP_FONT_14PX,
    15: BITMAP_FONT_15PX,
    16: BITMAP_FONT_16PX,
}


class TextComponent(Component):
    """
    Unified bitmap text component supporting 4-16px font heights.

    Features:
    - Supports font heights from 4px to 16px
    - Variable width per letter (optimized for each height)
    - Automatic letter spacing (1px for 4-7px, 2px for 8-16px)
    - Uppercase only (automatically converted)
    - Full character set: A-Z, 0-9, and 32 special characters
    - Optional background color and padding
    """

    def __init__(
        self,
        text: str,
        font_height: int = 5,
        fgcolor: Tuple[int, int, int] = (255, 255, 255),
        bgcolor: Tuple[int, int, int] | None = None,
        padding: int = 0
    ):
        """
        Initialize TextComponent.

        Args:
            text: Text to render (automatically converted to uppercase)
            font_height: Font height in pixels (4-16)
            fgcolor: Foreground (text) color RGB tuple
            bgcolor: Background color RGB tuple (None = transparent)
            padding: Padding around text in pixels

        Raises:
            ValueError: If font_height is not in range 4-16
        """
        super().__init__()

        # Validate font height
        if font_height not in FONT_MAP:
            available = ', '.join(map(str, sorted(FONT_MAP.keys())))
            raise ValueError(
                f"Font height {font_height}px not supported. "
                f"Available heights: {available}"
            )

        self.text = text.upper()
        self.font_height = font_height
        self.font = FONT_MAP[font_height]
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.padding = padding

        # Calculate letter spacing: 1px for smaller fonts (4-7px), 2px for larger (8-16px)
        self.letter_spacing = 1 if font_height < 8 else 2

        # Pre-compute dimensions (text size + padding)
        text_width, text_height = self._compute_text_dimensions()
        self._width = text_width + (2 * padding)
        self._height = text_height + (2 * padding)

    def _compute_text_dimensions(self) -> Tuple[int, int]:
        """Compute total width and height needed for text."""
        if not self.text:
            return (0, 0)

        total_width = 0
        for i, char in enumerate(self.text):
            if char in self.font:
                letter_width = self.font[char].shape[1]
                total_width += letter_width
                if i < len(self.text) - 1:  # Add spacing between letters
                    total_width += self.letter_spacing
            else:
                # Unknown character, use space
                total_width += self.font[' '].shape[1]
                if i < len(self.text) - 1:
                    total_width += self.letter_spacing

        return (total_width, self.font_height)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def compute_state(self, time: float) -> dict:
        """Compute state - static text, so state doesn't change with time."""
        return {
            'text': self.text,
            'font_height': self.font_height,
            'fgcolor': self.fgcolor,
            'bgcolor': self.bgcolor,
            'padding': self.padding
        }

    @cache_with_dict(maxsize=128)
    def _render_cached(self, state: dict, time: float) -> RenderBuffer:
        """Cached rendering of text. Time parameter not used (text is static)."""
        buffer = RenderBuffer(self._width, self._height)

        # Fill background if bgcolor is specified
        if self.bgcolor is not None:
            for y in range(self._height):
                for x in range(self._width):
                    buffer.set_pixel(x, y, self.bgcolor)

        if not self.text:
            return buffer

        # Render each letter (offset by padding)
        x_offset = self.padding
        for i, char in enumerate(self.text):
            letter_bitmap = self.font.get(char, self.font[' '])

            # Blit letter onto buffer
            self._blit_bitmap(buffer, letter_bitmap, x_offset, self.padding, self.fgcolor)

            # Move to next letter position
            x_offset += letter_bitmap.shape[1]
            if i < len(self.text) - 1:  # Add spacing
                x_offset += self.letter_spacing

        return buffer

    def _blit_bitmap(
        self,
        buffer: RenderBuffer,
        bitmap_array: np.ndarray,
        x_offset: int,
        y_offset: int,
        color: Tuple[int, int, int]
    ):
        """Blit bitmap array onto render buffer with color."""
        rows, cols = bitmap_array.shape

        for row in range(rows):
            for col in range(cols):
                if bitmap_array[row, col]:  # Pixel is on
                    x = x_offset + col
                    y = y_offset + row

                    if 0 <= x < buffer.width and 0 <= y < buffer.height:
                        buffer.set_pixel(x, y, color)
