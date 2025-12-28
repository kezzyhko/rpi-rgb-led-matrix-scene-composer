"""Base interface for display targets (terminal emulator, physical matrix, etc)."""

from abc import ABC, abstractmethod
from .render_buffer import RenderBuffer


class DisplayTarget(ABC):
    """Abstract base class for display targets."""

    @abstractmethod
    def initialize(self):
        """Initialize the display target."""
        pass

    @abstractmethod
    def display(self, buffer: RenderBuffer):
        """Display a rendered buffer."""
        pass

    @abstractmethod
    def shutdown(self):
        """Clean up and shutdown the display target."""
        pass

    @abstractmethod
    def get_dimensions(self):
        """
        Get the display dimensions.

        Returns:
            tuple: (width, height) in pixels
        """
        pass
