"""Physical RGB LED matrix display target (placeholder for rpi-rgb-led-matrix)."""

from .display_target import DisplayTarget
from .render_buffer import RenderBuffer


class RGBMatrixDisplayTarget(DisplayTarget):
    """
    Physical RGB LED matrix display target.

    This is a placeholder for the actual rpi-rgb-led-matrix implementation.
    Typical refresh rates on RPi: 100-400 Hz depending on configuration.
    """

    def __init__(self, width: int = 64, height: int = 32, **matrix_options):
        """
        Initialize RGB matrix display target.

        Args:
            width: Matrix width in pixels
            height: Matrix height in pixels
            **matrix_options: Additional options for RGBMatrix configuration
                            (e.g., hardware_mapping, rows, cols, chain_length,
                            parallel, pwm_bits, brightness, etc.)
        """
        self.width = width
        self.height = height
        self.matrix_options = matrix_options
        self.matrix = None
        self._initialized = False

    def initialize(self):
        """Initialize the physical RGB matrix."""
        if self._initialized:
            return

        try:
            from rgbmatrix import RGBMatrix, RGBMatrixOptions
        except ImportError:
            raise ImportError(
                "rpi-rgb-led-matrix library not found. "
                "Install with: pip install rpi-rgb-led-matrix"
            )

        # Configure matrix options
        options = RGBMatrixOptions()
        options.rows = self.matrix_options.get('rows', 32)
        options.cols = self.matrix_options.get('cols', 64)
        options.chain_length = self.matrix_options.get('chain_length', 1)
        options.parallel = self.matrix_options.get('parallel', 1)
        options.hardware_mapping = self.matrix_options.get('hardware_mapping', 'regular')
        options.pwm_bits = self.matrix_options.get('pwm_bits', 11)
        options.brightness = self.matrix_options.get('brightness', 100)
        options.pwm_lsb_nanoseconds = self.matrix_options.get('pwm_lsb_nanoseconds', 130)
        options.led_rgb_sequence = self.matrix_options.get('led_rgb_sequence', 'RGB')
        options.scan_mode = self.matrix_options.get('scan_mode', 0)

        # Create matrix
        self.matrix = RGBMatrix(options=options)
        self._initialized = True

    def display(self, buffer: RenderBuffer):
        """
        Display a rendered buffer on the physical matrix.

        Args:
            buffer: RenderBuffer to display
        """
        if not self._initialized:
            self.initialize()

        # Copy buffer pixels to matrix
        for y in range(min(self.height, buffer.height)):
            for x in range(min(self.width, buffer.width)):
                r, g, b = buffer.get_pixel(x, y)
                self.matrix.SetPixel(x, y, r, g, b)

    def shutdown(self):
        """Clean up the RGB matrix."""
        if not self._initialized:
            return

        if self.matrix:
            self.matrix.Clear()
            self.matrix = None

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
