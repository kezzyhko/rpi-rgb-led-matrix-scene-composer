"""Table component for rendering structured data on LED matrices."""

import numpy as np
from typing import List, Dict, Tuple, Type, Any
from .component import Component
from .render_buffer import RenderBuffer
from .text_component import Text4pxComponent, Text5pxComponent


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
    - Uses Text4pxComponent or Text5pxComponent for rendering
    """

    def __init__(
        self,
        data: List[Dict[str, Any]],
        headers: List[str] | None = None,
        col_widths: List[int] | None = None,
        text_component: Type = Text4pxComponent,
        fgcolor: Tuple[int, int, int] = (255, 255, 255),
        bgcolor: Tuple[int, int, int] | None = None,
        header_fgcolor: Tuple[int, int, int] | None = None,
        header_bgcolor: Tuple[int, int, int] | None = None,
        cell_padding: int = 1,
        show_borders: bool = True,
        show_headers: bool = True,
        border_color: Tuple[int, int, int] = (64, 64, 64)
    ):
        """
        Initialize TableComponent.

        Args:
            data: List of dictionaries, each representing a row
            headers: Column headers (if None, uses keys from first dict)
            col_widths: Width for each column in pixels (if None, auto-calculated)
            text_component: Text component class to use (Text4pxComponent or Text5pxComponent)
            fgcolor: Foreground color for data cells
            bgcolor: Background color for data cells (None = transparent)
            header_fgcolor: Foreground color for header row (None = use fgcolor)
            header_bgcolor: Background color for header row (None = use bgcolor)
            cell_padding: Padding within each cell in pixels
            show_borders: Whether to draw borders between cells
            show_headers: Whether to display header row (default True)
            border_color: Color of borders
        """
        super().__init__()

        self.data = data
        self.text_component = text_component
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.header_fgcolor = header_fgcolor if header_fgcolor is not None else fgcolor
        self.header_bgcolor = header_bgcolor if header_bgcolor is not None else bgcolor
        self.cell_padding = cell_padding
        self.show_borders = show_borders
        self.show_headers = show_headers
        self.border_color = border_color

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

        # Calculate total dimensions
        self._width = self._calculate_width()
        self._height = self._calculate_height()

        # Pre-render all text cells
        self._cell_cache = self._create_cell_cache()

    def _calculate_col_widths(self) -> List[int]:
        """Auto-calculate column widths based on content."""
        if not self.headers:
            return []

        col_widths = []

        for header in self.headers:
            max_width = 0

            # Check header width
            header_text = self.text_component(
                text=str(header).upper(),
                fgcolor=self.header_fgcolor,
                bgcolor=None,
                padding=0
            )
            max_width = max(max_width, header_text.width)

            # Check data widths
            for row in self.data:
                value = row.get(header, "")
                cell_text = self.text_component(
                    text=str(value).upper(),
                    fgcolor=self.fgcolor,
                    bgcolor=None,
                    padding=0
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
        dummy_text = self.text_component(
            text="X",
            fgcolor=self.fgcolor,
            bgcolor=None,
            padding=self.cell_padding
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
                text_comp = self.text_component(
                    text=str(header).upper(),
                    fgcolor=self.header_fgcolor,
                    bgcolor=self.header_bgcolor,
                    padding=self.cell_padding
                )
                cache[(0, col_idx)] = text_comp

        # Render data rows
        for row_idx, row_data in enumerate(self.data):
            # Offset by 1 if we're showing headers
            actual_row_idx = row_idx + (1 if self.show_headers else 0)

            for col_idx, header in enumerate(self.headers):
                value = row_data.get(header, "")
                text_comp = self.text_component(
                    text=str(value).upper(),
                    fgcolor=self.fgcolor,
                    bgcolor=self.bgcolor,
                    padding=self.cell_padding
                )
                cache[(actual_row_idx, col_idx)] = text_comp

        return cache

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def compute_state(self, time: float) -> dict:
        """Compute state - static table, doesn't change with time."""
        return {
            'data': str(self.data),  # Convert to string for hashability
            'headers': tuple(self.headers),
            'col_widths': tuple(self.col_widths)
        }

    def render(self, time: float) -> RenderBuffer:
        """Render table."""
        buffer = RenderBuffer(self._width, self._height)

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
                self._draw_horizontal_line(buffer, y_offset, self._width)
                y_offset += border_width

        return buffer

    def _blit_buffer(
        self,
        dest: RenderBuffer,
        src: RenderBuffer,
        x_offset: int,
        y_offset: int
    ):
        """Blit source buffer onto destination buffer at offset."""
        for y in range(src.height):
            for x in range(src.width):
                dest_x = x_offset + x
                dest_y = y_offset + y

                if 0 <= dest_x < dest.width and 0 <= dest_y < dest.height:
                    pixel = src.get_pixel(x, y)
                    dest.set_pixel(dest_x, dest_y, pixel)

    def _draw_vertical_line(
        self,
        buffer: RenderBuffer,
        x: int,
        y_start: int,
        height: int
    ):
        """Draw a vertical border line."""
        for y in range(y_start, y_start + height):
            if 0 <= x < buffer.width and 0 <= y < buffer.height:
                buffer.set_pixel(x, y, self.border_color)

    def _draw_horizontal_line(
        self,
        buffer: RenderBuffer,
        y: int,
        width: int
    ):
        """Draw a horizontal border line."""
        for x in range(width):
            if 0 <= x < buffer.width and 0 <= y < buffer.height:
                buffer.set_pixel(x, y, self.border_color)
