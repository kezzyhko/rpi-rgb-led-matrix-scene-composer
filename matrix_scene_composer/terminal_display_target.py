"""Lightweight terminal emulator for RGB LED matrix displays."""

import sys
from .display_target import DisplayTarget
from .render_buffer import RenderBuffer


class TerminalDisplayTarget(DisplayTarget):
    """
    Lightweight terminal-based display target using ANSI escape codes.

    Uses alternate screen buffer and double-buffering for flicker-free
    rendering at 30-60 FPS.
    """

    def __init__(self, width: int, height: int, use_half_blocks: bool = False, square_pixels: bool = True):
        """
        Initialize terminal display target.

        Args:
            width: Display width in pixels
            height: Display height in pixels
            use_half_blocks: If True, use Unicode half-blocks (▀/▄) to double
                           vertical resolution. If False, use full blocks (█)
            square_pixels: If True, render each pixel as 2 horizontal characters
                         to create square-ish pixels (terminal chars are typically ~2:1)
        """
        self.width = width
        self.height = height
        self.use_half_blocks = use_half_blocks
        self.square_pixels = square_pixels
        self._initialized = False

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

        # Single write for entire frame (reduces flicker)
        sys.stdout.write(''.join(frame))
        sys.stdout.flush()

    def _render_full_blocks(self, buffer: RenderBuffer, frame: list):
        """
        Render using full block characters (█).
        Each terminal character represents one LED pixel.
        """
        chars_per_pixel = 2 if self.square_pixels else 1

        for y in range(self.height):
            for x in range(self.width):
                r, g, b = buffer.get_pixel(x, y)
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
        """
        # Process two rows at a time
        for y in range(0, self.height, 2):
            for x in range(self.width):
                r1, g1, b1 = buffer.get_pixel(x, y)

                # Check if there's a second row
                if y + 1 < self.height:
                    r2, g2, b2 = buffer.get_pixel(x, y + 1)
                    # Upper half block: foreground is top pixel, background is bottom pixel
                    frame.append(f'\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀')
                else:
                    # Last row (odd height) - just show top pixel
                    frame.append(f'\x1b[38;2;{r1};{g1};{b1}m▀')

            # Reset colors and newline
            frame.append('\x1b[0m\n')

    def shutdown(self):
        """Clean up terminal display (show cursor, exit alternate screen)."""
        if not self._initialized:
            return

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
