"""Ultra-compact bitmap text component for LED matrix displays."""

from typing import Literal, Tuple

import numpy as np

from .bitmap_fonts import BITMAP_FONT_4PX, BITMAP_FONT_5PX
from .component import Component, cache_with_dict
from .render_buffer import RenderBuffer

# Font mapping for all available sizes
FONT_MAP = {
    4: BITMAP_FONT_4PX,
    5: BITMAP_FONT_5PX,
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
    - Automatic horizontal scrolling if text wider than max_width
    """

    def __init__(
        self,
        text: str,
        font_height: int = 5,
        fgcolor: Tuple[int, int, int] = (255, 255, 255),
        bgcolor: Tuple[int, int, int] | None = None,
        padding: int = 0,
        max_width: int | None = None,
        autoscroll: Literal["X", "NONE"] = "NONE",  # Text only scrolls horizontally
        scroll_speed: float = 20.0,
        scroll_pause: float = 1.0,
    ):
        """
        Initialize TextComponent.

        Args:
            text: Text to render (automatically converted to uppercase)
            font_height: Font height in pixels (4-16)
            fgcolor: Foreground (text) color RGB tuple
            bgcolor: Background color RGB tuple (None = transparent)
            padding: Padding around text in pixels
            max_width: Maximum width in pixels (None = no limit, scrolling disabled)
            scroll_speed: Scroll speed in pixels per second
            scroll_pause: Pause duration in seconds at start/end of scroll

        Raises:
            ValueError: If font_height is not in range 4-16
        """
        super().__init__()

        # Validate font height
        if font_height not in FONT_MAP:
            available = ", ".join(map(str, sorted(FONT_MAP.keys())))
            raise ValueError(
                f"Font height {font_height}px not supported. " f"Available heights: {available}"
            )

        self.text = text.upper()
        self.font_height = font_height
        self.font = FONT_MAP[font_height]
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.padding = padding
        self.max_width = max_width
        self.scroll_speed = scroll_speed
        self.scroll_pause = scroll_pause

        # Calculate letter spacing: 1px for smaller fonts (4-7px), 2px for larger (8-16px)
        self.letter_spacing = 1 if font_height < 8 else 2

        # Pre-compute text dimensions (without container constraint)
        text_width, text_height = self._compute_text_dimensions()
        self._text_width = text_width
        self._text_height = text_height

        self.autoscroll = autoscroll
        self._autoscroll_enabled = True  # Can be toggled at runtime
        self.scroll_offset_x = 0  # Manual scroll offset
        # determine if scrolling is needed
        self._needs_scroll = (
            autoscroll == "X" and max_width is not None and (text_width + 2 * padding) > max_width
        )

        # Set component dimensions
        if max_width is not None:
            self._width = max_width
        else:
            self._width = text_width + (2 * padding)
        self._height = text_height + (2 * padding)

        # Pre-render full text buffer (reused during scrolling)
        self._full_text_buffer = self._render_full_text()

    def _compute_text_dimensions(self) -> Tuple[int, int]:
        """Compute total width and height needed for text."""
        if not self.text:
            return (0, 0)

        total_width = 0
        for i, char in enumerate(self.text):
            if char in self.font:
                letter_width = self.font[char].shape[1]
                total_width += letter_width
                if i < len(self.text) - 1:
                    total_width += self.letter_spacing
            else:
                total_width += self.font[" "].shape[1]
                if i < len(self.text) - 1:
                    total_width += self.letter_spacing

        return (total_width, self.font_height)

    def _render_full_text(self) -> RenderBuffer:
        """Render complete text to buffer (used for scrolling)."""
        buffer = RenderBuffer(self._text_width, self._text_height)

        if not self.text:
            return buffer

        x_offset = 0
        for i, char in enumerate(self.text):
            letter_bitmap = self.font.get(char, self.font[" "])
            self._blit_bitmap(buffer, letter_bitmap, x_offset, 0, self.fgcolor)
            x_offset += letter_bitmap.shape[1]
            if i < len(self.text) - 1:
                x_offset += self.letter_spacing

        return buffer

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def compute_state(self, time: float) -> dict:
        """Compute state - includes scroll offset if scrolling is enabled."""
        if not self._needs_scroll:
            return {
                "text": self.text,
                "font_height": self.font_height,
                "fgcolor": self.fgcolor,
                "bgcolor": self.bgcolor,
                "padding": self.padding,
            }

        # Calculate scroll position
        if self.autoscroll == "X" and self._autoscroll_enabled:
            # Use time-based autoscroll
            scroll_offset = self._calculate_scroll_offset(time)
        else:
            # Use manual scroll offset
            scroll_offset = self.scroll_offset_x

        return {
            "text": self.text,
            "font_height": self.font_height,
            "fgcolor": self.fgcolor,
            "bgcolor": self.bgcolor,
            "padding": self.padding,
            "scroll_offset": int(scroll_offset),
        }

    def scroll_to(self, x: int = 0):
        """Set horizontal scroll position."""
        if not self._needs_scroll:
            return

        available_width = self._width - (2 * self.padding)
        max_scroll = max(0, self._text_width - available_width)
        self.scroll_offset_x = max(0, min(x, max_scroll))
        # Disable autoscroll when manually scrolling
        self._autoscroll_enabled = False

    def scroll_by(self, dx: int = 0):
        """Scroll by delta."""
        if not self._needs_scroll:
            return

        self.scroll_to(self.scroll_offset_x + dx)

    def can_scroll(self) -> bool:
        """Check if scrolling is possible."""
        return self._needs_scroll

    def is_focusable(self) -> bool:
        """Text component is focusable if it can scroll."""
        return self._needs_scroll

    def _calculate_scroll_offset(self, time: float) -> int:
        """Calculate horizontal scroll offset for given time."""
        # Available width for text (excluding padding)
        available_width = self._width - (2 * self.padding)

        # Total scroll distance (text width - available width)
        scroll_distance = self._text_width - available_width

        if scroll_distance <= 0:
            return 0

        # Total cycle time: pause + scroll right + pause + scroll left
        scroll_time = scroll_distance / self.scroll_speed
        cycle_time = (2 * self.scroll_pause) + (2 * scroll_time)

        # Position within current cycle
        t = time % cycle_time

        if t < self.scroll_pause:
            # Pause at start
            return 0
        elif t < self.scroll_pause + scroll_time:
            # Scroll right
            elapsed = t - self.scroll_pause
            return int(elapsed * self.scroll_speed)
        elif t < (2 * self.scroll_pause) + scroll_time:
            # Pause at end
            return scroll_distance
        else:
            # Scroll left
            elapsed = t - ((2 * self.scroll_pause) + scroll_time)
            return int(scroll_distance - (elapsed * self.scroll_speed))

    @cache_with_dict(maxsize=128)
    def _render_cached(self, state: dict, time: float) -> RenderBuffer:
        """Cached rendering of text with optional scrolling."""
        buffer = RenderBuffer(self._width, self._height)

        # Fill background if bgcolor is specified
        if self.bgcolor is not None:
            for y in range(self._height):
                for x in range(self._width):
                    buffer.set_pixel(x, y, self.bgcolor)

        if not self.text:
            return buffer

        if not self._needs_scroll:
            # No scrolling - render text directly at padding offset
            x_offset = self.padding
            for i, char in enumerate(self.text):
                letter_bitmap = self.font.get(char, self.font[" "])
                self._blit_bitmap(buffer, letter_bitmap, x_offset, self.padding, self.fgcolor)
                x_offset += letter_bitmap.shape[1]
                if i < len(self.text) - 1:
                    x_offset += self.letter_spacing
        else:
            # Scrolling - blit portion of pre-rendered text buffer
            scroll_offset = state["scroll_offset"]
            available_width = self._width - (2 * self.padding)

            # Copy visible portion from full text buffer
            for y in range(self._text_height):
                for x in range(available_width):
                    src_x = scroll_offset + x
                    if 0 <= src_x < self._text_width:
                        pixel = self._full_text_buffer.get_pixel(src_x, y)
                        dest_x = self.padding + x
                        dest_y = self.padding + y
                        if pixel[3] > 0:  # Only copy non-transparent pixels
                            buffer.set_pixel(dest_x, dest_y, pixel)

        return buffer

    def set_text(self, text: str, preserve_scroll: bool = True):
        """
        Update text content.

        Args:
            text: New text to display
            preserve_scroll: If True, maintains current scroll position
        """
        old_scroll = self.scroll_offset_x if preserve_scroll else 0

        self.text = text.upper()

        # Recalculate dimensions
        text_width, text_height = self._compute_text_dimensions()
        self._text_width = text_width
        self._text_height = text_height

        # Determine if scrolling is needed
        self._needs_scroll = (
            self.autoscroll == "X"
            and self.max_width is not None
            and (text_width + 2 * self.padding) > self.max_width
        )

        # Update component dimensions
        if self.max_width is not None:
            self._width = self.max_width
        else:
            self._width = text_width + (2 * self.padding)
        self._height = text_height + (2 * self.padding)

        # Re-render full text buffer
        self._full_text_buffer = self._render_full_text()

        # Restore or clamp scroll position
        if preserve_scroll and self._needs_scroll:
            available_width = self._width - (2 * self.padding)
            max_scroll = max(0, self._text_width - available_width)
            self.scroll_offset_x = min(old_scroll, max_scroll)
        else:
            self.scroll_offset_x = 0

    def _blit_bitmap(
        self,
        buffer: RenderBuffer,
        bitmap_array: np.ndarray,
        x_offset: int,
        y_offset: int,
        color: Tuple[int, int, int],
    ):
        """Blit bitmap array onto render buffer with color."""
        rows, cols = bitmap_array.shape

        for row in range(rows):
            for col in range(cols):
                if bitmap_array[row, col]:
                    x = x_offset + col
                    y = y_offset + row

                    if 0 <= x < buffer.width and 0 <= y < buffer.height:
                        buffer.set_pixel(x, y, color)
