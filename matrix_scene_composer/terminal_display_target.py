"""Lightweight terminal emulator for RGB LED matrix displays."""

import sys
import logging
from collections import deque
from .display_target import DisplayTarget
from .render_buffer import RenderBuffer


class LogCapture(logging.Handler):
    """Logging handler that captures the last N log messages."""

    def __init__(self, maxlen=10):
        super().__init__()
        self.log_lines = deque(maxlen=maxlen)
        self.formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(name)s - %(message)s', datefmt='%H:%M:%S')

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_lines.append(msg)
        except Exception:
            self.handleError(record)


class TerminalDisplayTarget(DisplayTarget):
    """
    Lightweight terminal-based display target using ANSI escape codes.

    Uses alternate screen buffer and double-buffering for flicker-free
    rendering at 30-60 FPS.
    """

    def __init__(self, width: int, height: int, use_half_blocks: bool = False, square_pixels: bool = True, show_logs: bool = True, log_lines: int = 10):
        """
        Initialize terminal display target.

        Args:
            width: Display width in pixels
            height: Display height in pixels
            use_half_blocks: If True, use Unicode half-blocks (▀/▄) to double
                           vertical resolution. If False, use full blocks (█)
            square_pixels: If True, render each pixel as 2 horizontal characters
                         to create square-ish pixels (terminal chars are typically ~2:1)
            show_logs: If True, show log lines below the matrix display
            log_lines: Number of recent log lines to show (default 10)
        """
        self.width = width
        self.height = height
        self.use_half_blocks = use_half_blocks
        self.square_pixels = square_pixels
        self.show_logs = show_logs
        self.log_lines_count = log_lines
        self._initialized = False

        # Setup log capture if requested
        self.log_capture = None
        if self.show_logs:
            self.log_capture = LogCapture(maxlen=log_lines)
            # Attach to root logger to capture all logs
            logging.getLogger().addHandler(self.log_capture)

    @property
    def size(self):
        """Return (width, height) tuple."""
        return (self.width, self.height)

    def initialize(self):
        """Initialize terminal display (enter alternate screen, hide cursor)."""
        if self._initialized:
            return

        # Enter alternate screen buffer
        sys.stdout.write('\x1b[?1049h')
        # Hide cursor
        sys.stdout.write('\x1b[?25l')
        # Clear screen
        sys.stdout.write('\x1b[2J')
        sys.stdout.flush()

        self._initialized = True

    def display(self, buffer: RenderBuffer):
        """
        Display a rendered buffer in the terminal.

        Args:
            buffer: RenderBuffer to display
        """
        if not self._initialized:
            self.initialize()

        frame = []
        # Move cursor to home position
        frame.append('\x1b[H')

        if self.use_half_blocks:
            self._render_half_blocks(buffer, frame)
        else:
            self._render_full_blocks(buffer, frame)

        # Add log lines below the matrix if enabled
        if self.show_logs and self.log_capture:
            self._render_log_section(frame)

        # Single write for entire frame (reduces flicker)
        sys.stdout.write(''.join(frame))
        sys.stdout.flush()

    def _render_full_blocks(self, buffer: RenderBuffer, frame: list):
        """
        Render using full block characters (█).
        Each terminal character represents one LED pixel.
        Alpha channel is flattened: fully transparent (alpha=0) shows as black,
        everything else shows its color.
        """
        chars_per_pixel = 2 if self.square_pixels else 1

        for y in range(self.height):
            for x in range(self.width):
                r, g, b, a = buffer.get_pixel(x, y)
                # Flatten alpha: if fully transparent, show black; otherwise show color
                if a == 0:
                    r, g, b = 0, 0, 0
                # Use background color and render multiple spaces for square pixels
                frame.append(f'\x1b[48;2;{r};{g};{b}m')
                frame.append(' ' * chars_per_pixel)
            # Reset colors and newline
            frame.append('\x1b[0m\n')

    def _render_half_blocks(self, buffer: RenderBuffer, frame: list):
        """
        Render using Unicode half-blocks (▀/▄).
        This doubles the vertical resolution by using foreground + background colors.
        Each terminal character represents two vertically stacked LED pixels.
        Alpha channel is flattened: fully transparent (alpha=0) shows as black,
        everything else shows its color.
        """
        # Process two rows at a time
        for y in range(0, self.height, 2):
            for x in range(self.width):
                r1, g1, b1, a1 = buffer.get_pixel(x, y)
                # Flatten alpha for top pixel
                if a1 == 0:
                    r1, g1, b1 = 0, 0, 0

                # Check if there's a second row
                if y + 1 < self.height:
                    r2, g2, b2, a2 = buffer.get_pixel(x, y + 1)
                    # Flatten alpha for bottom pixel
                    if a2 == 0:
                        r2, g2, b2 = 0, 0, 0
                    # Upper half block: foreground is top pixel, background is bottom pixel
                    frame.append(f'\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀')
                else:
                    # Last row (odd height) - just show top pixel
                    frame.append(f'\x1b[38;2;{r1};{g1};{b1}m▀')

            # Reset colors and newline
            frame.append('\x1b[0m\n')

    def _render_log_section(self, frame: list):
        """Render the log section below the matrix display."""
        # Reset colors and add blank line
        frame.append('\x1b[0m')
        frame.append('\n')

        # Calculate terminal width (matrix width * chars per pixel)
        chars_per_pixel = 2 if self.square_pixels else 1
        terminal_width = self.width * chars_per_pixel

        # Add log lines with clearing to full width
        if self.log_capture and self.log_capture.log_lines:
            for log_line in self.log_capture.log_lines:
                # Truncate or pad to terminal width
                if len(log_line) > terminal_width:
                    frame.append(log_line[:terminal_width])
                else:
                    frame.append(log_line)
                    frame.append(' ' * (terminal_width - len(log_line)))
                frame.append('\n')

    def shutdown(self):
        """Clean up terminal display (show cursor, exit alternate screen)."""
        if not self._initialized:
            return

        # Remove log handler
        if self.log_capture:
            logging.getLogger().removeHandler(self.log_capture)

        # Show cursor
        sys.stdout.write('\x1b[?25h')
        # Exit alternate screen buffer
        sys.stdout.write('\x1b[?1049l')
        sys.stdout.flush()

        self._initialized = False

    def get_dimensions(self):
        """
        Get display dimensions.

        Returns:
            tuple: (width, height) in pixels
        """
        return (self.width, self.height)

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()

    async def __aenter__(self):
        """Async context manager entry."""
        self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.shutdown()
        return False
