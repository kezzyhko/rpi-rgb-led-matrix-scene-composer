"""Image component for displaying bitmap images on LED matrix displays."""

from pathlib import Path
from typing import Dict, Any
import numpy as np
from PIL import Image

from .component import Component, cache_with_dict
from .render_buffer import RenderBuffer


class ImageComponent(Component):
    """
    Display a bitmap image.

    Loads common image formats (PNG, JPG, GIF, etc.) and renders them to the display.
    """

    def __init__(self, image_path: str | Path):
        """
        Initialize ImageComponent.

        Args:
            image_path: Path to image file
        """
        super().__init__()
        self.image_path = Path(image_path)

        # Load image
        img = Image.open(self.image_path)

        # Extract alpha channel if present
        if img.mode in ('RGBA', 'LA', 'PA'):
            # Convert to RGBA to ensure consistent alpha channel
            img_rgba = img.convert('RGBA')
            self._image_data = np.array(img_rgba, dtype=np.uint8)
            self._has_alpha = True
        else:
            # No alpha channel, convert to RGB
            img_rgb = img.convert('RGB')
            self._image_data = np.array(img_rgb, dtype=np.uint8)
            self._has_alpha = False

        self._height, self._width = self._image_data.shape[:2]

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def compute_state(self, time: float) -> Dict[str, Any]:
        """Compute state - static image, doesn't change with time."""
        return {
            'image_path': str(self.image_path),
        }

    @cache_with_dict(maxsize=128)
    def _render_cached(self, state: Dict[str, Any], time: float) -> RenderBuffer:
        """Cached rendering of the image. Time parameter not used (image is static)."""
        buffer = RenderBuffer(self._width, self._height)

        if self._has_alpha:
            # Direct copy of RGBA data
            buffer.data[:] = self._image_data
        else:
            # Copy RGB and set alpha to fully opaque
            buffer.data[:, :, :3] = self._image_data
            buffer.data[:, :, 3] = 255

        return buffer
