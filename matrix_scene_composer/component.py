"""Component base class and caching utilities."""

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Dict, List

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
            if not hasattr(self, "_render_cache"):
                self._render_cache = {}
                self._render_cache_maxsize = maxsize

            # Create cache key from state dict ONLY (ignore time)
            # Handle nested dicts by converting to nested tuples
            state_key = _make_hashable(state_dict)

            if state_key not in self._render_cache:
                if DEBUG:
                    component_name = self.__class__.__name__
                    print(
                        f"    [CACHE MISS] {component_name}._render_cached() - rendering new state"
                    )
                # Simple FIFO eviction when cache is full
                if len(self._render_cache) >= self._render_cache_maxsize:
                    self._render_cache.pop(next(iter(self._render_cache)))
                # Call func with both state_dict and time
                self._render_cache[state_key] = func(self, state_dict, time)
            else:
                if DEBUG:
                    component_name = self.__class__.__name__
                    print(
                        f"    [CACHE HIT] {component_name}._render_cached() - reusing cached buffer"
                    )

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
    - Focus support for interactive components
    - Debug rendering (focus outline)
    - Lifecycle hooks (mount, unmount, focus events)
    """

    # Class variable for debug rendering
    DEBUG_RENDER = False

    def __init__(self):
        """Initialize component."""
        self._rendered_at = 0.0  # Time when render output last changed
        self._last_state = None  # For detecting state changes
        self._focused = False  # Focus state
        self._mounted = False  # Mount state

        # Lifecycle callbacks
        self._on_mount_callbacks: List[Callable] = []
        self._on_unmount_callbacks: List[Callable] = []
        self._on_focus_gain_callbacks: List[Callable] = []
        self._on_focus_lost_callbacks: List[Callable] = []

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

    @property
    def focused(self) -> bool:
        """Check if component is focused."""
        return self._focused

    @property
    def mounted(self) -> bool:
        """Check if component is mounted."""
        return self._mounted

    def set_focus(self, focused: bool):
        """Set focus state and trigger lifecycle hooks."""
        if focused == self._focused:
            return

        old_focused = self._focused
        self._focused = focused

        # Trigger lifecycle hooks
        if focused and not old_focused:
            self._trigger_focus_gain()
        elif not focused and old_focused:
            self._trigger_focus_lost()

    def is_focusable(self) -> bool:
        """
        Check if component can receive focus.
        Override in subclasses for interactive components.
        """
        return False

    # Lifecycle hook registration
    def on_mount(self, callback: Callable):
        """Register callback for when component is mounted."""
        self._on_mount_callbacks.append(callback)

    def on_unmount(self, callback: Callable):
        """Register callback for when component is unmounted."""
        self._on_unmount_callbacks.append(callback)

    def on_focus_gain(self, callback: Callable):
        """Register callback for when component gains focus."""
        self._on_focus_gain_callbacks.append(callback)

    def on_focus_lost(self, callback: Callable):
        """Register callback for when component loses focus."""
        self._on_focus_lost_callbacks.append(callback)

    # Internal lifecycle triggers
    def _trigger_mount(self):
        """Trigger mount lifecycle hooks."""
        if self._mounted:
            return

        self._mounted = True
        for callback in self._on_mount_callbacks:
            callback()

    def _trigger_unmount(self):
        """Trigger unmount lifecycle hooks."""
        if not self._mounted:
            return

        self._mounted = False
        for callback in self._on_unmount_callbacks:
            callback()

    def _trigger_focus_gain(self):
        """Trigger focus gain lifecycle hooks."""
        for callback in self._on_focus_gain_callbacks:
            callback()

    def _trigger_focus_lost(self):
        """Trigger focus lost lifecycle hooks."""
        for callback in self._on_focus_lost_callbacks:
            callback()

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

        # Add focus state to invalidate cache when focus changes (only if debug render enabled)
        if Component.DEBUG_RENDER:
            state = dict(state) if state else {}
            state["_debug_focused"] = self._focused

        # Update timestamp if state changed (enables cache invalidation for parent components)
        if state != self._last_state:
            self._rendered_at = time
            self._last_state = state

        buffer = self._render_cached(state, time)

        # Apply debug rendering AFTER getting cached buffer
        # This modifies the buffer in-place, so we need to copy it first
        if Component.DEBUG_RENDER and self._focused:
            buffer = buffer.copy()
            buffer = self._apply_debug_render(buffer)

        return buffer

    def _apply_debug_render(self, buffer: RenderBuffer) -> RenderBuffer:
        """Apply debug rendering - draw purple outline around focused components."""
        # Purple color for focus outline
        focus_color = (128, 0, 255)

        # Draw top and bottom borders
        for x in range(buffer.width):
            buffer.set_pixel(x, 0, focus_color)
            if buffer.height > 1:
                buffer.set_pixel(x, buffer.height - 1, focus_color)

        # Draw left and right borders
        for y in range(buffer.height):
            buffer.set_pixel(0, y, focus_color)
            if buffer.width > 1:
                buffer.set_pixel(buffer.width - 1, y, focus_color)

        return buffer

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
