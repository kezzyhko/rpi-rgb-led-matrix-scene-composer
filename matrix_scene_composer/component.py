"""Component base class and caching utilities."""

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict
from .render_buffer import RenderBuffer

# Debug logging flag - set to True to see render pipeline details
DEBUG = False


def _make_hashable(obj):
    """Convert nested dicts/lists to hashable tuples recursively."""
    if isinstance(obj, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in obj.items()))
    elif isinstance(obj, list):
        return tuple(_make_hashable(item) for item in obj)
    elif isinstance(obj, tuple):
        return tuple(_make_hashable(item) for item in obj)
    else:
        return obj


def cache_with_dict(maxsize=128):
    """
    LRU cache decorator for instance methods that accept (state_dict, time) arguments.
    Caches ONLY by state_dict, ignoring time parameter.
    Each component instance has its own cache stored in self._render_cache.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, state_dict, time=None):
            # Initialize cache on first use
            if not hasattr(self, '_render_cache'):
                self._render_cache = {}
                self._render_cache_maxsize = maxsize

            # Create cache key from state dict ONLY (ignore time)
            # Handle nested dicts by converting to nested tuples
            state_key = _make_hashable(state_dict)

            if state_key not in self._render_cache:
                if DEBUG:
                    component_name = self.__class__.__name__
                    print(f"    [CACHE MISS] {component_name}._render_cached() - rendering new state")
                # Simple FIFO eviction when cache is full
                if len(self._render_cache) >= self._render_cache_maxsize:
                    self._render_cache.pop(next(iter(self._render_cache)))
                # Call func with both state_dict and time
                self._render_cache[state_key] = func(self, state_dict, time)
            else:
                if DEBUG:
                    component_name = self.__class__.__name__
                    print(f"    [CACHE HIT] {component_name}._render_cached() - reusing cached buffer")

            return self._render_cache[state_key]
        return wrapper
    return decorator


class Component(ABC):
    """
    Base class for all renderable components.

    Implements the compute_state() → _render_cached() pattern with:
    - Timestamp tracking (_rendered_at) for cache invalidation
    - State-based caching that ignores time parameter
    - Unified protocol for leaf and composite components
    """

    def __init__(self):
        """Initialize component."""
        self._rendered_at = 0.0  # Time when render output last changed
        self._last_state = None  # For detecting state changes

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

        IMPORTANT: Do NOT include 'time' in the returned dict.
        Time is passed separately to _render_cached to avoid cache invalidation every frame.
        """
        pass

    def render(self, time: float) -> RenderBuffer:
        """
        Render component at given time.
        Updates _rendered_at timestamp if state changed.
        Calls compute_state() then _render_cached().
        """
        state = self.compute_state(time)

        # Update timestamp if state changed (enables cache invalidation for parent components)
        if state != self._last_state:
            self._rendered_at = time
            self._last_state = state

        return self._render_cached(state, time)

    @abstractmethod
    def _render_cached(self, state: Dict[str, Any], time: float) -> RenderBuffer:
        """
        Render from state dict.
        Should use @cache_with_dict decorator for caching.

        Args:
            state: State dict from compute_state() (cache key)
            time: Current time (NOT part of cache key)

        Note: @cache_with_dict only caches by state dict, ignoring time parameter.
        """
        pass
