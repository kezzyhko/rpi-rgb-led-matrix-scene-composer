"""Table component for rendering structured data on LED matrices."""

from typing import Any, Dict, List, Literal, Tuple

import numpy as np

from .component import Component, cache_with_dict
from .render_buffer import RenderBuffer
from .text_component import TextComponent


class TableComponent(Component):
    """
    Table component for rendering structured data.

    Features:
    - Accepts list of dictionaries as data
    - Auto-derives headers from dictionary keys
    - Configurable column widths (auto-calculated if not provided)
    - Optional cell padding
    - Optional borders between cells/rows
    - Separate styling for header row
    - Uses TextComponent with configurable font height (4-16px)
    - Automatic or manual scrolling support
    """

    def __init__(
        self,
        data: List[Dict[str, Any]],
        headers: List[str] | None = None,
        col_widths: List[int] | None = None,
        font_height: int = 4,
        fgcolor: Tuple[int, int, int] = (255, 255, 255),
        bgcolor: Tuple[int, int, int] | None = None,
        header_fgcolor: Tuple[int, int, int] | None = None,
        header_bgcolor: Tuple[int, int, int] | None = None,
        cell_padding: int = 1,
        show_borders: bool = True,
        show_headers: bool = True,
        border_color: Tuple[int, int, int] = (64, 64, 64),
        max_width: int | None = None,
        max_height: int | None = None,
        autoscroll: Literal["X", "Y", "BOTH", "NONE"] = "NONE",
        scroll_speed: float = 20.0,
        scroll_pause: float = 1.0,
    ):
        """
        Initialize TableComponent.

        Args:
            data: List of dictionaries, each representing a row
            headers: Column headers (if None, uses keys from first dict)
            col_widths: Width for each column in pixels (if None, auto-calculated)
            font_height: Font height in pixels (4-16)
            fgcolor: Foreground color for data cells
            bgcolor: Background color for data cells (None = transparent)
            header_fgcolor: Foreground color for header row (None = use fgcolor)
            header_bgcolor: Background color for header row (None = use bgcolor)
            cell_padding: Padding within each cell in pixels
            show_borders: Whether to draw borders between cells
            show_headers: Whether to display header row (default True)
            border_color: Color of borders
            max_width: Maximum display width (enables horizontal scrolling if content wider)
            max_height: Maximum display height (enables vertical scrolling if content taller)
            autoscroll: Automatic scrolling direction ('X', 'Y', 'BOTH', 'NONE')
            scroll_speed: Auto-scroll speed in pixels per second
            scroll_pause: Pause duration at start/end of auto-scroll
        """
        super().__init__()

        self.data = data
        self.font_height = font_height
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.header_fgcolor = header_fgcolor if header_fgcolor is not None else fgcolor
        self.header_bgcolor = header_bgcolor if header_bgcolor is not None else bgcolor
        self.cell_padding = cell_padding
        self.show_borders = show_borders
        self.show_headers = show_headers
        self.border_color = border_color
        self.max_width = max_width
        self.max_height = max_height
        self.autoscroll = autoscroll
        self.scroll_speed = scroll_speed
        self.scroll_pause = scroll_pause

        # Manual scroll offsets
        self.scroll_offset_x = 0
        self.scroll_offset_y = 0

        # Derive headers from first dict if not provided
        if headers is None:
            if data:
                self.headers = list(data[0].keys())
            else:
                self.headers = []
        else:
            self.headers = headers

        # Auto-calculate column widths if not provided
        if col_widths is None:
            self.col_widths = self._calculate_col_widths()
        else:
            self.col_widths = col_widths

        # Calculate total table dimensions (full size)
        self._full_width = self._calculate_width()
        self._full_height = self._calculate_height()

        # Calculate display dimensions (viewport size)
        self._display_width = min(self._full_width, max_width) if max_width else self._full_width
        self._display_height = (
            min(self._full_height, max_height) if max_height else self._full_height
        )

        # Pre-render all text cells
        self._cell_cache = self._create_cell_cache()

        # Pre-render full table buffer (reused during scrolling)
        self._full_table_buffer = None

    def _calculate_col_widths(self) -> List[int]:
        """Auto-calculate column widths based on content."""
        if not self.headers:
            return []

        col_widths = []

        for header in self.headers:
            max_width = 0

            # Check header width
            header_text = TextComponent(
                text=str(header).upper(),
                font_height=self.font_height,
                fgcolor=self.header_fgcolor,
                bgcolor=None,
                padding=0,
            )
            max_width = max(max_width, header_text.width)

            # Check data widths
            for row in self.data:
                value = row.get(header, "")
                cell_text = TextComponent(
                    text=str(value).upper(),
                    font_height=self.font_height,
                    fgcolor=self.fgcolor,
                    bgcolor=None,
                    padding=0,
                )
                max_width = max(max_width, cell_text.width)

            # Add cell padding to width
            col_widths.append(max_width + (2 * self.cell_padding))

        return col_widths

    def _calculate_width(self) -> int:
        """Calculate total table width."""
        if not self.col_widths:
            return 0

        total_width = sum(self.col_widths)

        # Add border widths (1px between columns)
        if self.show_borders and len(self.col_widths) > 1:
            total_width += len(self.col_widths) - 1

        return total_width

    def _calculate_height(self) -> int:
        """Calculate total table height."""
        if not self.data:
            return 0

        # Get row height from text component
        dummy_text = TextComponent(
            text="X",
            font_height=self.font_height,
            fgcolor=self.fgcolor,
            bgcolor=None,
            padding=self.cell_padding,
        )
        row_height = dummy_text.height

        # Total rows = header (if shown) + data rows
        num_rows = len(self.data) + (1 if self.show_headers else 0)
        total_height = num_rows * row_height

        # Add border heights (1px between rows)
        if self.show_borders and num_rows > 1:
            total_height += num_rows - 1

        return total_height

    def _create_cell_cache(self) -> Dict[Tuple[int, int], Component]:
        """Pre-render all cells into cache."""
        cache = {}

        # Render header row (if enabled)
        if self.show_headers:
            for col_idx, header in enumerate(self.headers):
                text_comp = TextComponent(
                    text=str(header).upper(),
                    font_height=self.font_height,
                    fgcolor=self.header_fgcolor,
                    bgcolor=self.header_bgcolor,
                    padding=self.cell_padding,
                )
                cache[(0, col_idx)] = text_comp

        # Render data rows
        for row_idx, row_data in enumerate(self.data):
            # Offset by 1 if we're showing headers
            actual_row_idx = row_idx + (1 if self.show_headers else 0)

            for col_idx, header in enumerate(self.headers):
                value = row_data.get(header, "")
                text_comp = TextComponent(
                    text=str(value).upper(),
                    font_height=self.font_height,
                    fgcolor=self.fgcolor,
                    bgcolor=self.bgcolor,
                    padding=self.cell_padding,
                )
                cache[(actual_row_idx, col_idx)] = text_comp

        return cache

    def _render_full_table(self, time: float) -> RenderBuffer:
        """Render complete table to buffer (used for scrolling)."""
        if self._full_table_buffer is not None:
            return self._full_table_buffer

        buffer = RenderBuffer(self._full_width, self._full_height)

        # Calculate row height
        if not self._cell_cache:
            return buffer

        # Get a sample cell to determine row height
        sample_cell = next(iter(self._cell_cache.values()))
        row_height = sample_cell.height
        border_width = 1 if self.show_borders else 0

        y_offset = 0

        # Render each row
        num_rows = len(self.data) + (1 if self.show_headers else 0)
        for row_idx in range(num_rows):
            x_offset = 0

            # Render each column in this row
            for col_idx in range(len(self.headers)):
                cell_key = (row_idx, col_idx)

                if cell_key in self._cell_cache:
                    cell_component = self._cell_cache[cell_key]
                    cell_buffer = cell_component.render(time)

                    # Blit cell onto table buffer
                    self._blit_buffer(buffer, cell_buffer, x_offset, y_offset)

                # Move to next column
                x_offset += self.col_widths[col_idx]

                # Add vertical border
                if self.show_borders and col_idx < len(self.headers) - 1:
                    self._draw_vertical_line(buffer, x_offset, y_offset, row_height)
                    x_offset += border_width

            # Move to next row
            y_offset += row_height

            # Add horizontal border
            if self.show_borders and row_idx < num_rows - 1:
                self._draw_horizontal_line(buffer, y_offset, self._full_width)
                y_offset += border_width

        self._full_table_buffer = buffer
        return buffer

    def _calculate_scroll_offset(self, time: float, direction: Literal["X", "Y"]) -> int:
        """Calculate scroll offset for given time and direction."""
        if direction == "X":
            available_size = self._display_width
            total_size = self._full_width
        else:  # Y
            available_size = self._display_height
            total_size = self._full_height

        scroll_distance = total_size - available_size

        if scroll_distance <= 0:
            return 0

        # Total cycle time: pause + scroll + pause + scroll back
        scroll_time = scroll_distance / self.scroll_speed
        cycle_time = (2 * self.scroll_pause) + (2 * scroll_time)

        # Position within current cycle
        t = time % cycle_time

        if t < self.scroll_pause:
            # Pause at start
            return 0
        elif t < self.scroll_pause + scroll_time:
            # Scroll forward
            elapsed = t - self.scroll_pause
            return int(elapsed * self.scroll_speed)
        elif t < (2 * self.scroll_pause) + scroll_time:
            # Pause at end
            return scroll_distance
        else:
            # Scroll back
            elapsed = t - ((2 * self.scroll_pause) + scroll_time)
            return int(scroll_distance - (elapsed * self.scroll_speed))

    @property
    def width(self) -> int:
        return self._display_width

    @property
    def height(self) -> int:
        return self._display_height

    def scroll_to(self, x: int = 0, y: int = 0):
        """Set scroll position."""
        max_scroll_x = max(0, self._full_width - self._display_width)
        max_scroll_y = max(0, self._full_height - self._display_height)
        self.scroll_offset_x = max(0, min(x, max_scroll_x))
        self.scroll_offset_y = max(0, min(y, max_scroll_y))

    def scroll_by(self, dx: int = 0, dy: int = 0):
        """Scroll by delta."""
        self.scroll_to(self.scroll_offset_x + dx, self.scroll_offset_y + dy)

    def can_scroll_horizontal(self) -> bool:
        """Check if horizontal scrolling is possible."""
        return self.max_width is not None and self._full_width > self._display_width

    def can_scroll_vertical(self) -> bool:
        """Check if vertical scrolling is possible."""
        return self.max_height is not None and self._full_height > self._display_height

    def is_focusable(self) -> bool:
        """Table component is focusable if it can scroll."""
        return self.can_scroll_horizontal() or self.can_scroll_vertical()

    def compute_state(self, time: float) -> dict:
        """Compute state - includes scroll offsets if scrolling is enabled."""
        state = {
            "data": str(self.data),
            "headers": tuple(self.headers),
            "col_widths": tuple(self.col_widths),
        }

        # Add auto-scroll offsets to state
        if self.autoscroll in ("X", "BOTH"):
            state["autoscroll_x"] = self._calculate_scroll_offset(time, "X")

        if self.autoscroll in ("Y", "BOTH"):
            state["autoscroll_y"] = self._calculate_scroll_offset(time, "Y")

        # Add manual scroll offsets
        state["scroll_x"] = self.scroll_offset_x
        state["scroll_y"] = self.scroll_offset_y

        return state

    @cache_with_dict(maxsize=128)
    def _render_cached(self, state: Dict[str, Any], time: float) -> RenderBuffer:
        """Render table viewport (cached)."""
        # Get full table buffer
        full_buffer = self._render_full_table(time)

        # Determine effective scroll offsets (auto + manual)
        scroll_x = state.get("scroll_x", 0)
        scroll_y = state.get("scroll_y", 0)

        if self.autoscroll in ("X", "BOTH"):
            scroll_x += state.get("autoscroll_x", 0)

        if self.autoscroll in ("Y", "BOTH"):
            scroll_y += state.get("autoscroll_y", 0)

        # Clamp scroll offsets
        max_scroll_x = max(0, self._full_width - self._display_width)
        max_scroll_y = max(0, self._full_height - self._display_height)
        scroll_x = max(0, min(scroll_x, max_scroll_x))
        scroll_y = max(0, min(scroll_y, max_scroll_y))

        # Create viewport buffer
        viewport = RenderBuffer(self._display_width, self._display_height)

        # Copy visible portion from full buffer
        for y in range(self._display_height):
            for x in range(self._display_width):
                src_x = scroll_x + x
                src_y = scroll_y + y
                if 0 <= src_x < self._full_width and 0 <= src_y < self._full_height:
                    pixel = full_buffer.get_pixel(src_x, src_y)
                    viewport.set_pixel(x, y, pixel)

        return viewport

    def _blit_buffer(self, dest: RenderBuffer, src: RenderBuffer, x_offset: int, y_offset: int):
        """Blit source buffer onto destination buffer at offset."""
        for y in range(src.height):
            for x in range(src.width):
                dest_x = x_offset + x
                dest_y = y_offset + y

                if 0 <= dest_x < dest.width and 0 <= dest_y < dest.height:
                    pixel = src.get_pixel(x, y)
                    dest.set_pixel(dest_x, dest_y, pixel)

    def _draw_vertical_line(self, buffer: RenderBuffer, x: int, y_start: int, height: int):
        """Draw a vertical border line."""
        for y in range(y_start, y_start + height):
            if 0 <= x < buffer.width and 0 <= y < buffer.height:
                buffer.set_pixel(x, y, self.border_color)

    def _draw_horizontal_line(self, buffer: RenderBuffer, y: int, width: int):
        """Draw a horizontal border line."""
        for x in range(width):
            if 0 <= x < buffer.width and 0 <= y < buffer.height:
                buffer.set_pixel(x, y, self.border_color)
