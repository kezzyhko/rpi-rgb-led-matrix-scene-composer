"""Scrollbar component for LED matrix displays."""

from typing import Tuple, Literal
from .component import Component, cache_with_dict
from .render_buffer import RenderBuffer


class Scrollbar(Component):
    """
    Scrollbar component for indicating scroll position.

    Features:
    - Horizontal or vertical orientation
    - Configurable colors for track, thumb, and arrows
    - Automatically calculates thumb size based on viewport/content ratio
    """

    def __init__(
        self,
        width: int,
        height: int,
        orientation: Literal["horizontal", "vertical"] = "vertical",
        viewport_size: int = 100,
        content_size: int = 200,
        scroll_position: int = 0,
        track_color: Tuple[int, int, int] = (32, 32, 32),
        thumb_color: Tuple[int, int, int] = (128, 128, 128),
        arrow_color: Tuple[int, int, int] | None = (64, 64, 64),
        min_thumb_size: int = 3,
    ):
        """
        Initialize Scrollbar.

        Args:
            width: Scrollbar width in pixels
            height: Scrollbar height in pixels
            orientation: Scrollbar orientation ('horizontal' or 'vertical')
            viewport_size: Size of visible area
            content_size: Total size of content
            scroll_position: Current scroll position (0 to content_size - viewport_size)
            track_color: Background track color
            thumb_color: Draggable thumb color
            arrow_color: Arrow indicators color (None = no arrows)
            min_thumb_size: Minimum thumb size in pixels
        """
        super().__init__()

        self._width = width
        self._height = height
        self.orientation = orientation
        self.viewport_size = viewport_size
        self.content_size = content_size
        self.scroll_position = scroll_position
        self.track_color = track_color
        self.thumb_color = thumb_color
        self.arrow_color = arrow_color
        self.min_thumb_size = min_thumb_size

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def set_scroll_position(self, position: int):
        """Set scroll position."""
        max_scroll = max(0, self.content_size - self.viewport_size)
        self.scroll_position = max(0, min(position, max_scroll))

    def set_content_size(self, size: int):
        """Update content size."""
        self.content_size = size
        self.set_scroll_position(self.scroll_position)  # Clamp position

    def compute_state(self, time: float) -> dict:
        """Compute state - scroll position and sizes."""
        return {
            "viewport_size": self.viewport_size,
            "content_size": self.content_size,
            "scroll_position": self.scroll_position,
        }

    @cache_with_dict(maxsize=128)
    def _render_cached(self, state: dict, time: float) -> RenderBuffer:
        """Render scrollbar."""
        buffer = RenderBuffer(self._width, self._height)

        viewport_size = state["viewport_size"]
        content_size = state["content_size"]
        scroll_position = state["scroll_position"]

        # Draw track background
        for y in range(self._height):
            for x in range(self._width):
                buffer.set_pixel(x, y, self.track_color)

        # Calculate thumb dimensions
        if content_size <= viewport_size:
            # No scrolling needed - show full thumb
            if self.orientation == "vertical":
                thumb_size = self._height
                thumb_position = 0
            else:
                thumb_size = self._width
                thumb_position = 0
        else:
            # Calculate thumb size proportional to viewport/content ratio
            max_scroll = content_size - viewport_size

            if self.orientation == "vertical":
                track_size = self._height
                arrow_space = 2 if self.arrow_color else 0
                available_track = track_size - (2 * arrow_space)

                thumb_size = max(
                    self.min_thumb_size, int(available_track * (viewport_size / content_size))
                )
                thumb_travel = available_track - thumb_size

                if max_scroll > 0:
                    thumb_position = arrow_space + int(
                        thumb_travel * (scroll_position / max_scroll)
                    )
                else:
                    thumb_position = arrow_space
            else:  # horizontal
                track_size = self._width
                arrow_space = 2 if self.arrow_color else 0
                available_track = track_size - (2 * arrow_space)

                thumb_size = max(
                    self.min_thumb_size, int(available_track * (viewport_size / content_size))
                )
                thumb_travel = available_track - thumb_size

                if max_scroll > 0:
                    thumb_position = arrow_space + int(
                        thumb_travel * (scroll_position / max_scroll)
                    )
                else:
                    thumb_position = arrow_space

        # Draw thumb
        if self.orientation == "vertical":
            for y in range(thumb_position, min(thumb_position + thumb_size, self._height)):
                for x in range(self._width):
                    buffer.set_pixel(x, y, self.thumb_color)
        else:  # horizontal
            for x in range(thumb_position, min(thumb_position + thumb_size, self._width)):
                for y in range(self._height):
                    buffer.set_pixel(x, y, self.thumb_color)

        # Draw arrows
        if self.arrow_color:
            if self.orientation == "vertical":
                # Up arrow (top)
                mid_x = self._width // 2
                buffer.set_pixel(mid_x, 0, self.arrow_color)
                if self._width >= 3:
                    buffer.set_pixel(mid_x - 1, 1, self.arrow_color)
                    buffer.set_pixel(mid_x + 1, 1, self.arrow_color)

                # Down arrow (bottom)
                if self._width >= 3:
                    buffer.set_pixel(mid_x - 1, self._height - 2, self.arrow_color)
                    buffer.set_pixel(mid_x + 1, self._height - 2, self.arrow_color)
                buffer.set_pixel(mid_x, self._height - 1, self.arrow_color)
            else:  # horizontal
                # Left arrow
                mid_y = self._height // 2
                buffer.set_pixel(0, mid_y, self.arrow_color)
                if self._height >= 3:
                    buffer.set_pixel(1, mid_y - 1, self.arrow_color)
                    buffer.set_pixel(1, mid_y + 1, self.arrow_color)

                # Right arrow
                if self._height >= 3:
                    buffer.set_pixel(self._width - 2, mid_y - 1, self.arrow_color)
                    buffer.set_pixel(self._width - 2, mid_y + 1, self.arrow_color)
                buffer.set_pixel(self._width - 1, mid_y, self.arrow_color)

        return buffer
