"""Progress bar component for LED matrix displays."""

from typing import Tuple, Optional, Literal
from .component import Component, cache_with_dict
from .render_buffer import RenderBuffer
from .text_component import TextComponent


class ProgressBar(Component):
    """
    Progress bar component with optional label.

    Features:
    - Horizontal or vertical orientation
    - Configurable colors for filled/unfilled portions
    - Optional text label showing percentage or custom text
    - Border support
    """

    def __init__(
        self,
        width: int,
        height: int,
        progress: float = 0.0,
        orientation: Literal["horizontal", "vertical"] = "horizontal",
        fill_color: Tuple[int, int, int] = (0, 255, 0),
        empty_color: Tuple[int, int, int] = (32, 32, 32),
        border_color: Tuple[int, int, int] | None = (64, 64, 64),
        show_label: bool = False,
        label_text: str | None = None,
        label_font_height: int = 4,
        label_color: Tuple[int, int, int] = (255, 255, 255),
    ):
        """
        Initialize ProgressBar.

        Args:
            width: Bar width in pixels
            height: Bar height in pixels
            progress: Progress value from 0.0 to 1.0
            orientation: Bar orientation ('horizontal' or 'vertical')
            fill_color: Color of filled portion
            empty_color: Color of empty portion
            border_color: Border color (None = no border)
            show_label: Whether to show text label
            label_text: Custom label text (None = show percentage)
            label_font_height: Font height for label (4-16)
            label_color: Label text color
        """
        super().__init__()

        self._width = width
        self._height = height
        self.progress = max(0.0, min(1.0, progress))
        self.orientation = orientation
        self.fill_color = fill_color
        self.empty_color = empty_color
        self.border_color = border_color
        self.show_label = show_label
        self.label_text = label_text
        self.label_font_height = label_font_height
        self.label_color = label_color

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def set_progress(self, progress: float):
        """Set progress value (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, progress))

    def compute_state(self, time: float) -> dict:
        """Compute state - progress value and label."""
        return {
            "progress": round(self.progress, 3),
            "show_label": self.show_label,
            "label_text": self.label_text,
        }

    @cache_with_dict(maxsize=128)
    def _render_cached(self, state: dict, time: float) -> RenderBuffer:
        """Render progress bar."""
        buffer = RenderBuffer(self._width, self._height)

        progress = state["progress"]

        # Calculate bar area (accounting for border)
        border_width = 1 if self.border_color else 0
        bar_x = border_width
        bar_y = border_width
        bar_width = self._width - (2 * border_width)
        bar_height = self._height - (2 * border_width)

        # Calculate fill dimensions
        if self.orientation == "horizontal":
            fill_width = int(bar_width * progress)

            # Draw filled portion
            for y in range(bar_y, bar_y + bar_height):
                for x in range(bar_x, bar_x + fill_width):
                    buffer.set_pixel(x, y, self.fill_color)

            # Draw empty portion
            for y in range(bar_y, bar_y + bar_height):
                for x in range(bar_x + fill_width, bar_x + bar_width):
                    buffer.set_pixel(x, y, self.empty_color)

        else:  # vertical
            # Vertical bars fill from bottom to top
            fill_height = int(bar_height * progress)
            empty_start_y = bar_y
            fill_start_y = bar_y + bar_height - fill_height

            # Draw empty portion (top)
            for y in range(empty_start_y, fill_start_y):
                for x in range(bar_x, bar_x + bar_width):
                    buffer.set_pixel(x, y, self.empty_color)

            # Draw filled portion (bottom)
            for y in range(fill_start_y, bar_y + bar_height):
                for x in range(bar_x, bar_x + bar_width):
                    buffer.set_pixel(x, y, self.fill_color)

        # Draw border
        if self.border_color:
            # Top and bottom
            for x in range(self._width):
                buffer.set_pixel(x, 0, self.border_color)
                buffer.set_pixel(x, self._height - 1, self.border_color)

            # Left and right
            for y in range(self._height):
                buffer.set_pixel(0, y, self.border_color)
                buffer.set_pixel(self._width - 1, y, self.border_color)

        # Draw label
        if self.show_label:
            label_text = state.get("label_text")
            if label_text is None:
                label_text = f"{int(progress * 100)}%"

            label_comp = TextComponent(
                text=label_text,
                font_height=self.label_font_height,
                fgcolor=self.label_color,
                padding=0,
            )

            # Center label
            label_buffer = label_comp.render(time)
            label_x = (self._width - label_buffer.width) // 2
            label_y = (self._height - label_buffer.height) // 2

            buffer.blit(label_buffer, (label_x, label_y))

        return buffer
