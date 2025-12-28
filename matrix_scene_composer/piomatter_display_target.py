"""PioMatter display target for Adafruit RGB Matrix Bonnet on Raspberry Pi 5."""

import numpy as np
from .display_target import DisplayTarget
from .render_buffer import RenderBuffer


class PioMatterDisplayTarget(DisplayTarget):
    """
    Display target for Adafruit RGB Matrix Bonnet using PioMatter library.

    Optimized for Raspberry Pi 5 with direct numpy array transfers.
    Typical refresh rates: 60+ FPS depending on panel configuration.
    """

    def __init__(
        self,
        width: int = 64,
        height: int = 32,
        n_addr_lines: int = 4,
        brightness: float = 1.0,
        **piomatter_options
    ):
        """
        Initialize PioMatter display target.

        Args:
            width: Matrix width in pixels
            height: Matrix height in pixels
            n_addr_lines: Number of address lines (4 for 64x32, 5 for 64x64)
            brightness: Brightness multiplier (0.0-1.0)
            **piomatter_options: Additional options for PioMatter configuration
        """
        self.width = width
        self.height = height
        self.n_addr_lines = n_addr_lines
        self.brightness = brightness
        self.piomatter_options = piomatter_options
        self.matrix = None
        self.framebuffer = None
        self._initialized = False

    def initialize(self):
        """Initialize the PioMatter matrix."""
        if self._initialized:
            return

        try:
            import adafruit_blinka_raspberry_pi5_piomatter as piomatter
        except ImportError:
            raise ImportError(
                "adafruit_blinka_raspberry_pi5_piomatter library not found. "
                "Install with: pip install adafruit-blinka-raspberry-pi5-piomatter"
            )

        # Configure geometry (matching working adafruit_diagnostic.py pattern)
        geometry = piomatter.Geometry(
            width=self.width,
            height=self.height,
            n_addr_lines=self.n_addr_lines,
            rotation=piomatter.Orientation.Normal  # Use Normal orientation
        )

        # Create framebuffer (height, width, 3) - matches RenderBuffer shape!
        # Initialize as zeros (matching working example)
        self.framebuffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Create matrix instance (matching working example)
        self.matrix = piomatter.PioMatter(
            colorspace=piomatter.Colorspace.RGB888Packed,
            pinout=piomatter.Pinout.AdafruitMatrixBonnet,
            framebuffer=self.framebuffer,
            geometry=geometry
        )

        self._initialized = True

    def display(self, buffer: RenderBuffer):
        """
        Display a rendered buffer on the physical matrix.

        Optimized with direct numpy array assignment for zero-copy transfer.

        Args:
            buffer: RenderBuffer to display
        """
        if not self._initialized:
            self.initialize()

        # Optimized: Direct numpy array copy with optional brightness adjustment
        if self.brightness < 1.0:
            # Apply brightness with vectorized operation
            np.multiply(buffer.data, self.brightness, out=self.framebuffer, casting='unsafe')
        else:
            # Zero-copy assignment using memoryview
            self.framebuffer[:] = buffer.data

        # Push to hardware
        self.matrix.show()

    def shutdown(self):
        """Clean up the PioMatter matrix."""
        if not self._initialized:
            return

        if self.framebuffer is not None:
            # Clear display
            self.framebuffer[:] = 0
            if self.matrix is not None:
                self.matrix.show()

        self.matrix = None
        self.framebuffer = None
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
