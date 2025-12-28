"""RenderBuffer - Fixed-size RGB pixel buffer."""

import numpy as np
from typing import Tuple


class RenderBuffer:
    """Fixed-size RGBA pixel buffer using numpy."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # Shape: (height, width, 4), RGBA, uint8
        # Alpha channel: 0=transparent, 255=opaque
        self.data = np.zeros((height, width, 4), dtype=np.uint8)
        # Default to fully opaque
        self.data[:, :, 3] = 255

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int] | Tuple[int, int, int, int]):
        """Set pixel at (x, y) to color (r, g, b) or (r, g, b, a)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if len(color) == 3:
                self.data[y, x, :3] = color
                # Keep existing alpha
            else:
                self.data[y, x] = color

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """Get pixel color at (x, y) as (r, g, b, a)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return tuple(self.data[y, x])
        return (0, 0, 0, 0)

    def clear(self, color: Tuple[int, int, int] | Tuple[int, int, int, int] = (0, 0, 0, 0)):
        """Clear buffer to color (r, g, b) or (r, g, b, a). Default is transparent black."""
        if len(color) == 3:
            self.data[:, :, :3] = color
            self.data[:, :, 3] = 255  # Opaque
        else:
            self.data[:, :] = color

    def blit(self, source: 'RenderBuffer', position: Tuple[int, int], opacity: float = 1.0):
        """
        Blit (copy) source buffer onto this buffer at position with alpha compositing.
        Automatically clips if source extends beyond bounds.
        Uses standard alpha compositing: blends source over destination using source's alpha channel.
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

        # Get regions
        src_region = source.data[src_y_start:src_y_end, src_x_start:src_x_end].astype(float)
        dst_region = self.data[dst_y_start:dst_y_end, dst_x_start:dst_x_end].astype(float)

        # Extract alpha (0-255) and normalize to 0-1
        src_alpha = src_region[:, :, 3:4] / 255.0 * opacity

        # Alpha compositing: out = src * alpha + dst * (1 - alpha)
        # RGB channels
        blended_rgb = dst_region[:, :, :3] * (1 - src_alpha) + src_region[:, :, :3] * src_alpha

        # Alpha channel: out_alpha = src_alpha + dst_alpha * (1 - src_alpha)
        dst_alpha = dst_region[:, :, 3:4] / 255.0
        blended_alpha = src_alpha + dst_alpha * (1 - src_alpha)

        # Combine and write back
        self.data[dst_y_start:dst_y_end, dst_x_start:dst_x_end, :3] = blended_rgb.astype(np.uint8)
        self.data[dst_y_start:dst_y_end, dst_x_start:dst_x_end, 3:4] = (blended_alpha * 255).astype(np.uint8)

    def copy(self) -> 'RenderBuffer':
        """Create a copy of this buffer."""
        new_buffer = RenderBuffer(self.width, self.height)
        new_buffer.data = self.data.copy()
        return new_buffer
