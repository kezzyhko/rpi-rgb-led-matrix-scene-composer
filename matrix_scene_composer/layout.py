"""Layout components for automatic positioning of child components."""

from typing import Any, Dict, List, Literal, Optional, Tuple

from .component import Component, cache_with_dict
from .render_buffer import RenderBuffer


class Layout(Component):
    """
    Base class for layout components that automatically position children.

    Layouts are components that manage positioning of child components.
    Add layouts to scenes, add components to layouts.
    """

    def __init__(self, width: int, height: int):
        super().__init__()
        self._width = width
        self._height = height
        self.children: List[Tuple[str, Component]] = []
        self._positions: Dict[str, Tuple[int, int]] = {}

        # Focus management
        self._focused_child: Optional[str] = None
        self._focusable_children: List[str] = []

    def add(self, child_id: str, component: Component):
        """Add a component to this layout."""
        self.children.append((child_id, component))

        # Update focusable children list
        if component.is_focusable():
            self._focusable_children.append(child_id)
            # Auto-focus first focusable component if nothing focused yet
            if self._focused_child is None:
                self.set_focused_component(child_id)

        self._recalculate_positions()

    def is_focusable(self) -> bool:
        """Layout is focusable if it has focusable children."""
        return len(self._focusable_children) > 0

    def get_focused(self) -> Optional[str]:
        """Get ID of currently focused child."""
        return self._focused_child

    def get_focused_component(self) -> Optional[Component]:
        """Get currently focused component instance."""
        if self._focused_child:
            for child_id, component in self.children:
                if child_id == self._focused_child:
                    return component
        return None

    def set_focused_component(self, child_id: str):
        """Set focus to specific child."""
        found = False
        component = None
        for cid, comp in self.children:
            if cid == child_id:
                found = True
                component = comp
                break

        if component is None:
            return

        if not found or not component.is_focusable():
            return

        # Clear focus from previous child
        if self._focused_child:
            for cid, comp in self.children:
                if cid == self._focused_child:
                    comp.set_focus(False)
                    break

        # Set focus to new child
        self._focused_child = child_id
        component.set_focus(True)

    def focus_next(self):
        """Focus next focusable component in order."""
        if not self._focusable_children:
            return

        if self._focused_child is None:
            self.set_focused_component(self._focusable_children[0])
            return

        try:
            current_idx = self._focusable_children.index(self._focused_child)
            next_idx = (current_idx + 1) % len(self._focusable_children)
            self.set_focused_component(self._focusable_children[next_idx])
        except ValueError:
            self.set_focused_component(self._focusable_children[0])

    def focus_previous(self):
        """Focus previous focusable component in order."""
        if not self._focusable_children:
            return

        if self._focused_child is None:
            self.set_focused_component(self._focusable_children[-1])
            return

        try:
            current_idx = self._focusable_children.index(self._focused_child)
            prev_idx = (current_idx - 1) % len(self._focusable_children)
            self.set_focused_component(self._focusable_children[prev_idx])
        except ValueError:
            self.set_focused_component(self._focusable_children[-1])

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def _recalculate_positions(self):
        """Calculate positions for all children. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _recalculate_positions")

    def compute_state(self, time: float) -> dict:
        """Compute state including child states and positions."""
        child_states = {}
        for child_id, component in self.children:
            from .component import _make_hashable

            child_states[child_id] = {
                "state": _make_hashable(component.compute_state(time)),
                "position": self._positions.get(child_id, (0, 0)),
            }
        return {"children": child_states}

    @cache_with_dict(maxsize=32)
    def _render_cached(self, state: dict, time: float) -> RenderBuffer:
        """Render all children at their calculated positions."""
        buffer = RenderBuffer(self._width, self._height)

        for child_id, component in self.children:
            child_buffer = component.render(time)
            position = self._positions.get(child_id, (0, 0))
            buffer.blit(child_buffer, position)

        return buffer


class VStack(Layout):
    """
    Vertical stack layout - arranges children top to bottom.

    Args:
        width: Container width
        height: Container height
        spacing: Vertical spacing between children (default: 2)
        alignment: Horizontal alignment ('left', 'center', 'right')
        padding: Padding around edges (default: 0)
    """

    def __init__(
        self,
        width: int,
        height: int,
        spacing: int = 2,
        alignment: Literal["left", "center", "right"] = "left",
        padding: int = 0,
    ):
        super().__init__(width, height)
        self.spacing = spacing
        self.alignment = alignment
        self.padding = padding

    def _recalculate_positions(self):
        """Calculate vertical stack positions."""
        self._positions = {}
        current_y = self.padding

        for child_id, component in self.children:
            # Calculate x position based on alignment
            if self.alignment == "left":
                x = self.padding
            elif self.alignment == "center":
                x = (self._width - component.width) // 2
            else:  # right
                x = self._width - component.width - self.padding

            self._positions[child_id] = (x, current_y)
            current_y += component.height + self.spacing


class HStack(Layout):
    """
    Horizontal stack layout - arranges children left to right.

    Args:
        width: Container width
        height: Container height
        spacing: Horizontal spacing between children (default: 2)
        alignment: Vertical alignment ('top', 'center', 'bottom')
        padding: Padding around edges (default: 0)
    """

    def __init__(
        self,
        width: int,
        height: int,
        spacing: int = 2,
        alignment: Literal["top", "center", "bottom"] = "top",
        padding: int = 0,
    ):
        super().__init__(width, height)
        self.spacing = spacing
        self.alignment = alignment
        self.padding = padding

    def _recalculate_positions(self):
        """Calculate horizontal stack positions."""
        self._positions = {}
        current_x = self.padding

        for child_id, component in self.children:
            # Calculate y position based on alignment
            if self.alignment == "top":
                y = self.padding
            elif self.alignment == "center":
                y = (self._height - component.height) // 2
            else:  # bottom
                y = self._height - component.height - self.padding

            self._positions[child_id] = (current_x, y)
            current_x += component.width + self.spacing


class Grid(Layout):
    """
    Grid layout - arranges children in rows and columns.

    Args:
        width: Container width
        height: Container height
        columns: Number of columns
        spacing: Spacing between cells (default: 2)
        padding: Padding around edges (default: 0)
    """

    def __init__(self, width: int, height: int, columns: int, spacing: int = 2, padding: int = 0):
        super().__init__(width, height)
        self.columns = columns
        self.spacing = spacing
        self.padding = padding

    def _recalculate_positions(self):
        """Calculate grid positions."""
        self._positions = {}

        if not self.children:
            return

        # Calculate cell dimensions
        available_width = self._width - (2 * self.padding) - ((self.columns - 1) * self.spacing)
        cell_width = available_width // self.columns

        rows = (len(self.children) + self.columns - 1) // self.columns
        available_height = self._height - (2 * self.padding) - ((rows - 1) * self.spacing)
        cell_height = available_height // rows

        for idx, (child_id, component) in enumerate(self.children):
            row = idx // self.columns
            col = idx % self.columns

            x = self.padding + col * (cell_width + self.spacing)
            y = self.padding + row * (cell_height + self.spacing)

            # Center component within cell
            x += (cell_width - component.width) // 2
            y += (cell_height - component.height) // 2

            self._positions[child_id] = (x, y)


class Absolute(Layout):
    """
    Absolute positioning layout - manual positioning with helper methods.

    Provides convenience methods for common positioning patterns while
    allowing explicit control when needed.
    """

    def __init__(self, width: int, height: int):
        super().__init__(width, height)
        self._manual_positions: Dict[str, Tuple[int, int]] = {}

    def add(self, child_id: str, component: Component, position: Optional[Tuple[int, int]] = None):
        """Add component with optional position."""
        self.children.append((child_id, component))
        if position is not None:
            self._manual_positions[child_id] = position
        self._recalculate_positions()

    def _recalculate_positions(self):
        """Use manually set positions."""
        self._positions = self._manual_positions.copy()

    def place(self, child_id: str, x: int, y: int):
        """Set explicit position for a child."""
        self._manual_positions[child_id] = (x, y)
        self._recalculate_positions()

    def center(self, child_id: str):
        """Center a child component."""
        for cid, component in self.children:
            if cid == child_id:
                x = (self._width - component.width) // 2
                y = (self._height - component.height) // 2
                self._manual_positions[child_id] = (x, y)
                self._recalculate_positions()
                return

    def align_top_left(self, child_id: str, padding: int = 0):
        """Align component to top-left corner."""
        self._manual_positions[child_id] = (padding, padding)
        self._recalculate_positions()

    def align_top_right(self, child_id: str, padding: int = 0):
        """Align component to top-right corner."""
        for cid, component in self.children:
            if cid == child_id:
                x = self._width - component.width - padding
                self._manual_positions[child_id] = (x, padding)
                self._recalculate_positions()
                return

    def align_bottom_left(self, child_id: str, padding: int = 0):
        """Align component to bottom-left corner."""
        for cid, component in self.children:
            if cid == child_id:
                y = self._height - component.height - padding
                self._manual_positions[child_id] = (padding, y)
                self._recalculate_positions()
                return

    def align_bottom_right(self, child_id: str, padding: int = 0):
        """Align component to bottom-right corner."""
        for cid, component in self.children:
            if cid == child_id:
                x = self._width - component.width - padding
                y = self._height - component.height - padding
                self._manual_positions[child_id] = (x, y)
                self._recalculate_positions()
                return


class ZStack(Layout):
    """
    Z-stack layout - layers children on top of each other.

    All children positioned at same location (typically centered).
    Useful for overlays, backgrounds, and layered effects.

    Args:
        width: Container width
        height: Container height
        alignment: Position alignment ('center', 'top-left', 'top-right', 'bottom-left', 'bottom-right')
        padding: Padding from edges when using corner alignment (default: 0)
    """

    def __init__(
        self,
        width: int,
        height: int,
        alignment: Literal[
            "center", "top-left", "top-right", "bottom-left", "bottom-right"
        ] = "center",
        padding: int = 0,
    ):
        super().__init__(width, height)
        self.alignment = alignment
        self.padding = padding

    def _recalculate_positions(self):
        """Calculate stacked positions based on alignment."""
        self._positions = {}

        for child_id, component in self.children:
            if self.alignment == "center":
                x = (self._width - component.width) // 2
                y = (self._height - component.height) // 2
            elif self.alignment == "top-left":
                x = self.padding
                y = self.padding
            elif self.alignment == "top-right":
                x = self._width - component.width - self.padding
                y = self.padding
            elif self.alignment == "bottom-left":
                x = self.padding
                y = self._height - component.height - self.padding
            else:  # bottom-right
                x = self._width - component.width - self.padding
                y = self._height - component.height - self.padding

            self._positions[child_id] = (x, y)
