"""Component base class and caching utilities."""

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict
from .render_buffer import RenderBuffer

# Debug logging flag - set to True to see render pipeline details
DEBUG = False


def cache_with_dict(maxsize=128):
    """
    LRU cache decorator for instance methods that accept dict arguments.
    Each component instance has its own cache stored in self._render_cache.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, state_dict):
            # Initialize cache on first use
            if not hasattr(self, '_render_cache'):
                self._render_cache = {}
                self._render_cache_maxsize = maxsize

            # Create cache key from state dict
            state_key = tuple(sorted(state_dict.items()))

            if state_key not in self._render_cache:
                if DEBUG:
                    component_name = self.__class__.__name__
                    print(f"    [CACHE MISS] {component_name}._render_cached() - rendering new state")
                # Simple FIFO eviction when cache is full
                if len(self._render_cache) >= self._render_cache_maxsize:
                    self._render_cache.pop(next(iter(self._render_cache)))
                self._render_cache[state_key] = func(self, state_dict)
            else:
                if DEBUG:
                    component_name = self.__class__.__name__
                    print(f"    [CACHE HIT] {component_name}._render_cached() - reusing cached buffer")

            return self._render_cache[state_key]
        return wrapper
    return decorator


class Component(ABC):
    """Base class for all renderable components."""

    def __init__(self):
        """Initialize component."""
        pass

    @property
    @abstractmethod
    def width(self) -> int:
        """Component width in pixels."""
        pass

    @property
    @abstractmethod
    def height(self) -> int:
        """Component height in pixels."""
        pass

    @abstractmethod
    def compute_state(self, time: float) -> Dict[str, Any]:
        """
        Compute component state at given time.
        Must return a dict with all values that affect rendering.
        Dict values must be hashable (int, float, str, tuple, etc).
        """
        pass

    @abstractmethod
    def render(self, time: float) -> RenderBuffer:
        """
        Render component at given time.
        Should call compute_state() then _render_cached().
        """
        pass
