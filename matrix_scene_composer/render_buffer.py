"""RenderBuffer - Fixed-size RGB pixel buffer."""

import numpy as np
from typing import Tuple


class RenderBuffer:
    """Fixed-size RGB pixel buffer using numpy."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # Shape: (height, width, 3), RGB, uint8
        self.data = np.zeros((height, width, 3), dtype=np.uint8)

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """Set pixel at (x, y) to color (r, g, b)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.data[y, x] = color

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get pixel color at (x, y)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return tuple(self.data[y, x])
        return (0, 0, 0)

    def clear(self, color: Tuple[int, int, int] = (0, 0, 0)):
        """Clear buffer to color."""
        self.data[:, :] = color

    def blit(self, source: 'RenderBuffer', position: Tuple[int, int], opacity: float = 1.0):
        """
        Blit (copy) source buffer onto this buffer at position.
        Automatically clips if source extends beyond bounds.
        """
        x_offset, y_offset = position

        # Calculate visible region
        src_x_start = max(0, -x_offset)
        src_y_start = max(0, -y_offset)
        src_x_end = min(source.width, self.width - x_offset)
        src_y_end = min(source.height, self.height - y_offset)

        dst_x_start = max(0, x_offset)
        dst_y_start = max(0, y_offset)

        # Nothing to blit if completely out of bounds
        if src_x_start >= src_x_end or src_y_start >= src_y_end:
            return

        dst_x_end = dst_x_start + (src_x_end - src_x_start)
        dst_y_end = dst_y_start + (src_y_end - src_y_start)

        if opacity >= 1.0:
            # Direct copy
            self.data[dst_y_start:dst_y_end, dst_x_start:dst_x_end] = \
                source.data[src_y_start:src_y_end, src_x_start:src_x_end]
        else:
            # Alpha blending
            src_region = source.data[src_y_start:src_y_end, src_x_start:src_x_end].astype(float)
            dst_region = self.data[dst_y_start:dst_y_end, dst_x_start:dst_x_end].astype(float)
            blended = dst_region * (1 - opacity) + src_region * opacity
            self.data[dst_y_start:dst_y_end, dst_x_start:dst_x_end] = blended.astype(np.uint8)

    def copy(self) -> 'RenderBuffer':
        """Create a copy of this buffer."""
        new_buffer = RenderBuffer(self.width, self.height)
        new_buffer.data = self.data.copy()
        return new_buffer
