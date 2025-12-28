"""Ultra-compact bitmap text components for LED matrix displays."""

import numpy as np
from typing import Tuple
from .component import Component, cache_with_dict
from .render_buffer import RenderBuffer
from .bitmap_fonts import BITMAP_FONT_4PX, BITMAP_FONT_5PX


class Text4pxComponent(Component):
    """
    Ultra-compact 4px height bitmap text component.

    Features:
    - Fixed 4px height
    - Variable width per letter (1-5px)
    - 1px spacing between letters
    - Uppercase only
    - Supports A-Z, 0-9, space, !, ., :
    """

    def __init__(
        self,
        text: str,
        fgcolor: Tuple[int, int, int] = (255, 255, 255),
        bgcolor: Tuple[int, int, int] | None = None,
        padding: int = 0
    ):
        """
        Initialize Text4pxComponent.

        Args:
            text: Text to render (automatically converted to uppercase)
            fgcolor: Foreground (text) color RGB tuple
            bgcolor: Background color RGB tuple (None = transparent)
            padding: Padding around text in pixels
        """
        super().__init__()
        self.text = text.upper()
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.padding = padding

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
            if char in BITMAP_FONT_4PX:
                letter_width = BITMAP_FONT_4PX[char].shape[1]
                total_width += letter_width
                if i < len(self.text) - 1:  # Add spacing between letters
                    total_width += 1
            else:
                # Unknown character, use space
                total_width += BITMAP_FONT_4PX[' '].shape[1]
                if i < len(self.text) - 1:
                    total_width += 1

        return (total_width, 4)

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
            'fgcolor': self.fgcolor,
            'bgcolor': self.bgcolor,
            'padding': self.padding
        }

    def render(self, time: float) -> RenderBuffer:
        """Render text."""
        state = self.compute_state(time)
        return self._render_cached(state)

    @cache_with_dict(maxsize=128)
    def _render_cached(self, state) -> RenderBuffer:
        """Cached rendering of text."""
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
            if char in BITMAP_FONT_4PX:
                letter_bitmap = BITMAP_FONT_4PX[char]
            else:
                # Unknown character, use space
                letter_bitmap = BITMAP_FONT_4PX[' ']

            # Blit letter onto buffer
            self._blit_bitmap(buffer, letter_bitmap, x_offset, self.padding, self.fgcolor)

            # Move to next letter position
            x_offset += letter_bitmap.shape[1]
            if i < len(self.text) - 1:  # Add spacing
                x_offset += 1

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


class Text5pxComponent(Component):
    """
    Compact 5px height bitmap text component.

    Features:
    - Fixed 5px height
    - Variable width per letter (1-5px)
    - 1px spacing between letters
    - Uppercase only
    - Supports A-Z, 0-9, space, !, ., :
    - Slightly more readable than 4px version
    """

    def __init__(
        self,
        text: str,
        fgcolor: Tuple[int, int, int] = (255, 255, 255),
        bgcolor: Tuple[int, int, int] | None = None,
        padding: int = 0
    ):
        """
        Initialize Text5pxComponent.

        Args:
            text: Text to render (automatically converted to uppercase)
            fgcolor: Foreground (text) color RGB tuple
            bgcolor: Background color RGB tuple (None = transparent)
            padding: Padding around text in pixels
        """
        super().__init__()
        self.text = text.upper()
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.padding = padding

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
            if char in BITMAP_FONT_5PX:
                letter_width = BITMAP_FONT_5PX[char].shape[1]
                total_width += letter_width
                if i < len(self.text) - 1:  # Add spacing between letters
                    total_width += 1
            else:
                # Unknown character, use space
                total_width += BITMAP_FONT_5PX[' '].shape[1]
                if i < len(self.text) - 1:
                    total_width += 1

        return (total_width, 5)

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
            'fgcolor': self.fgcolor,
            'bgcolor': self.bgcolor,
            'padding': self.padding
        }

    def render(self, time: float) -> RenderBuffer:
        """Render text."""
        state = self.compute_state(time)
        return self._render_cached(state)

    @cache_with_dict(maxsize=128)
    def _render_cached(self, state) -> RenderBuffer:
        """Cached rendering of text."""
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
            if char in BITMAP_FONT_5PX:
                letter_bitmap = BITMAP_FONT_5PX[char]
            else:
                # Unknown character, use space
                letter_bitmap = BITMAP_FONT_5PX[' ']

            # Blit letter onto buffer
            self._blit_bitmap(buffer, letter_bitmap, x_offset, self.padding, self.fgcolor)

            # Move to next letter position
            x_offset += letter_bitmap.shape[1]
            if i < len(self.text) - 1:  # Add spacing
                x_offset += 1

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
