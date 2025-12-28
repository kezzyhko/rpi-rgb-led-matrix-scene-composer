"""Scene - Container for components with positioning and layering."""

from typing import Dict, Tuple, Optional
from .component import Component, DEBUG
from .render_buffer import RenderBuffer


class ComponentInstance:
    """Wrapper for component with positioning and rendering properties."""

    def __init__(self, component: Component, position: Tuple[int, int], z_index: int, opacity: float):
        self.component = component
        self.position = position
        self.z_index = z_index
        self.opacity = opacity


class Scene:
    """Container for components with fixed canvas size."""

    def __init__(self, width: int, height: int, orchestrator=None):
        """
        Initialize scene.

        Args:
            width: Scene canvas width
            height: Scene canvas height
            orchestrator: Optional parent orchestrator (provides global time)
                        If None, scene manages its own time
        """
        self.width = width
        self.height = height
        self.orchestrator = orchestrator
        self.components: Dict[str, ComponentInstance] = {}
        self.canvas = RenderBuffer(width, height)
        self._internal_time = 0.0  # Used when no orchestrator

    @property
    def time(self) -> float:
        """Get current time (from orchestrator or internal)."""
        if self.orchestrator:
            return self.orchestrator.time
        return self._internal_time

    def add_component(
        self,
        component_id: str,
        component: Component,
        position: Tuple[int, int] = (0, 0),
        z_index: int = 0,
        opacity: float = 1.0
    ):
        """
        Add component to scene.

        Args:
            component_id: Unique identifier for this component
            component: Component instance
            position: (x, y) position in scene
            z_index: Layer order (higher = on top)
            opacity: Component opacity (0.0 to 1.0)
        """
        self.components[component_id] = ComponentInstance(
            component=component,
            position=position,
            z_index=z_index,
            opacity=opacity
        )

    def remove_component(self, component_id: str):
        """Remove component from scene."""
        if component_id in self.components:
            del self.components[component_id]

    def render(self, time: float) -> RenderBuffer:
        """
        Render all components to scene canvas.

        Args:
            time: Global time in seconds

        Returns:
            RenderBuffer with all components rendered
        """
        if DEBUG:
            print(f" Scene.render(time={time:.2f}) - rendering {len(self.components)} components")

        # Clear canvas
        self.canvas.clear()

        # Sort components by z_index (low to high)
        sorted_instances = sorted(
            self.components.values(),
            key=lambda inst: inst.z_index
        )

        # Render each component
        for comp_id, instance in [(id, inst) for id, inst in self.components.items()]:
            if DEBUG:
                component_name = instance.component.__class__.__name__
                print(f"  Rendering component '{comp_id}' ({component_name}) at position {instance.position}")

            # Get component to render itself
            component_buffer = instance.component.render(time)

            # Blit component buffer to scene canvas at position
            self.canvas.blit(
                component_buffer,
                instance.position,
                instance.opacity
            )

        return self.canvas

    def on_enter(self):
        """Called when scene becomes active."""
        pass

    def on_exit(self):
        """Called when scene is deactivated."""
        pass
