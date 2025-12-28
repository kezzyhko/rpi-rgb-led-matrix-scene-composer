"""Scene - Composite component container with positioning, layering, and animations."""

import asyncio
import time
import logging
from typing import Dict, Tuple, Optional, List, Callable
from .component import Component, cache_with_dict, DEBUG
from .render_buffer import RenderBuffer

# Setup logging to file
logging.basicConfig(
    filename="/tmp/animation_demo.log",
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class ComponentInstance:
    """Component instance in a scene with state (x, y, opacity, z_index)."""

    def __init__(self, component: Component, **state):
        self.component = component
        self.state = state  # Dict: {x, y, opacity, z_index, ...}


class Scene(Component):
    """
    Composite component - renders child components with positioning and animations.

    Inherits from Component, implementing the same compute_state → _render_cached protocol.
    Manages focus for interactive components.
    """

    def __init__(
        self,
        width: int = None,
        height: int = None,
        size: Tuple[int, int] = None,
        entrance_animations: Optional[List] = None,
        idle_animations: Optional[List] = None,
        exit_animations: Optional[List] = None,
    ):
        """
        Initialize scene.

        Args:
            width: Scene canvas width
            height: Scene canvas height
            size: Tuple of (width, height) - alternative to width/height
            entrance_animations: List of (start_time, animation) tuples to run when scene enters
            idle_animations: List of (start_time, animation) tuples for continuous animations
            exit_animations: List of (start_time, animation) tuples to run when scene exits
        """
        super().__init__()

        # Determine width and height
        if size is not None:
            self._width, self._height = size
        elif width is not None and height is not None:
            self._width = width
            self._height = height
        else:
            raise ValueError("Must provide either 'size' or both 'width' and 'height'")

        self.children: Dict[str, ComponentInstance] = {}
        self.canvas = RenderBuffer(self._width, self._height)

        # Focus management
        self._focused_child: Optional[str] = None
        self._focusable_children: List[str] = []

        # Animation phases - built-in phases
        self.entrance_animations = entrance_animations or []
        self.idle_animations = idle_animations or []
        self.exit_animations = exit_animations or []

        # Custom animation phases - user-defined
        self._custom_phases: Dict[str, List[Tuple[float, "Animation"]]] = {}

        # Current active animations
        self.current_animations: List[Tuple[float, "Animation"]] = []
        self._scene_start_time: Optional[float] = None
        self._current_phase: Optional[str] = None

        # Standalone mode (without orchestrator)
        self._display_callback: Optional[Callable[[RenderBuffer], None]] = None
        self._running = False
        self._time = 0.0
        self._fps = 30

    @property
    def width(self) -> int:
        """Scene width in pixels."""
        return self._width

    @property
    def height(self) -> int:
        """Scene height in pixels."""
        return self._height

    def add_child(
        self,
        child_id: str,
        component: Component,
        position: Optional[Tuple[int, int]] = None,
        **state,
    ):
        """
        Add child component to scene.

        Args:
            child_id: Unique identifier for this child
            component: Component instance
            position: Optional (x, y) tuple for position (alternative to x=, y= kwargs)
            **state: Scene state for this child (x, y, opacity, z_index, etc.)

        Example:
            scene.add_child("text1", text_comp, x=10, y=10, opacity=1.0, z_index=0)
            scene.add_child("text2", text_comp, position=(10, 10))
        """
        if position is not None:
            state["x"] = position[0]
            state["y"] = position[1]

        self.children[child_id] = ComponentInstance(component, **state)

        # Trigger mount lifecycle
        component._trigger_mount()

        # Update focusable children list
        if component.is_focusable():
            self._focusable_children.append(child_id)
            # Auto-focus first focusable component if nothing focused yet
            if self._focused_child is None:
                self.set_focus(child_id)

    def remove_child(self, child_id: str):
        """Remove child component from scene."""
        if child_id in self.children:
            component = self.children[child_id].component

            # Trigger unmount lifecycle
            component._trigger_unmount()

            del self.children[child_id]

            # Update focus if we removed the focused child
            if self._focused_child == child_id:
                self._focused_child = None
                if self._focusable_children:
                    self.set_focus(self._focusable_children[0])

            # Update focusable list
            if child_id in self._focusable_children:
                self._focusable_children.remove(child_id)

    def reset(self):
        """Reset scene to initial state for re-entry."""
        self._time = 0.0
        self._scene_start_time = None
        self._current_phase = None
        self.clear_animations()

        # Reset all animations
        for anim_list in [self.entrance_animations, self.idle_animations, self.exit_animations]:
            for _, anim in anim_list:
                anim.reset()

        for phase_anims in self._custom_phases.values():
            for _, anim in phase_anims:
                anim.reset()

    def get_focused(self) -> Optional[str]:
        """Get ID of currently focused child."""
        return self._focused_child

    def get_focused_component(self) -> Optional[Component]:
        """Get currently focused component instance."""
        if self._focused_child and self._focused_child in self.children:
            return self.children[self._focused_child].component
        return None

    def set_focus(self, child_id: str):
        """Set focus to specific child."""
        if child_id not in self.children:
            return

        component = self.children[child_id].component
        if not component.is_focusable():
            return

        # Clear focus from previous child
        if self._focused_child and self._focused_child in self.children:
            self.children[self._focused_child].component.set_focus(False)

        # Set focus to new child
        self._focused_child = child_id
        component.set_focus(True)

    def focus_next(self):
        """Focus next focusable component in order."""
        if not self._focusable_children:
            return

        if self._focused_child is None:
            self.set_focus(self._focusable_children[0])
            return

        try:
            current_idx = self._focusable_children.index(self._focused_child)
            next_idx = (current_idx + 1) % len(self._focusable_children)
            self.set_focus(self._focusable_children[next_idx])
        except ValueError:
            self.set_focus(self._focusable_children[0])

    def focus_previous(self):
        """Focus previous focusable component in order."""
        if not self._focusable_children:
            return

        if self._focused_child is None:
            self.set_focus(self._focusable_children[-1])
            return

        try:
            current_idx = self._focusable_children.index(self._focused_child)
            prev_idx = (current_idx - 1) % len(self._focusable_children)
            self.set_focus(self._focusable_children[prev_idx])
        except ValueError:
            self.set_focus(self._focusable_children[-1])

    def add_animation(self, animation: "Animation", start_time: float = 0.0):
        """Add animation to current animations."""
        self.current_animations.append((start_time, animation))

    def clear_animations(self):
        """Clear all current animations."""
        self.current_animations.clear()

    def compute_state(self, time: float) -> dict:
        """
        Compute scene state: child positions/opacities + render timestamps.

        Scene state includes:
        - Child state (position, opacity, z_index) with animations applied
        - Child render timestamps (for cache invalidation)

        Does NOT include:
        - Time (would invalidate cache every frame)
        - Component internal state (respects encapsulation)
        """
        scene_time = self._time if hasattr(self, "_time") else 0.0

        child_states = {}

        for child_id, instance in self.children.items():
            # Apply animations using the Animation's own update() method
            for start_time, anim in self.current_animations:
                if anim.target == child_id:
                    elapsed = max(0.0, scene_time - start_time)
                    anim.update(instance.state, elapsed)

            # Build state dict for rendering (includes child component state for cache invalidation)
            state = instance.state.copy()
            child_component_state = instance.component.compute_state(time)
            from .component import _make_hashable

            state["_child_state"] = _make_hashable(child_component_state)

            child_states[child_id] = state

        return {"children": child_states}

    @cache_with_dict(maxsize=32)
    def _render_cached(self, state: dict, time: float) -> RenderBuffer:
        """
        Render scene from state dict - CACHED!

        Cache invalidates when:
        - Any child position/opacity/z_index changes (state dict different)
        - Any child component re-renders (_rendered_at timestamp changed)

        Cache hits when:
        - All child state unchanged
        - All child _rendered_at timestamps unchanged
        """
        canvas = RenderBuffer(self._width, self._height)
        canvas.clear()

        # Sort by z_index
        sorted_children = sorted(
            state["children"].items(), key=lambda item: item[1].get("z_index", 0)
        )

        # Composite children
        for child_id, child_state in sorted_children:
            instance = self.children[child_id]

            # Child renders itself (uses its own cache)
            buffer = instance.component.render(time)

            # Composite with child's state
            x = int(child_state.get("x", 0))
            y = int(child_state.get("y", 0))

            canvas.blit(buffer, (x, y), child_state.get("opacity", 1.0))

        return canvas

    def register_animation_phase(
        self, phase_name: str, animations: List[Tuple[float, "Animation"]]
    ):
        """Register a custom animation phase."""
        self._custom_phases[phase_name] = animations
        logger.info(
            f"Registered custom animation phase '{phase_name}' with {len(animations)} animation(s)"
        )

    def set_animation_phase(self, phase: Optional[str]):
        """Set the current animation phase."""
        current_scene_time = self._time if hasattr(self, "_time") else 0.0

        if phase is None:
            logger.debug(f"set_animation_phase(None) - clearing all animations")
            self._current_phase = None
            self.clear_animations()
        else:
            logger.debug(f"set_animation_phase('{phase}') at scene_time={current_scene_time:.3f}")
            self._start_phase(phase, current_scene_time)

    def _start_phase(self, phase: str, current_scene_time: float = 0.0):
        """Internal method to start an animation phase."""
        self._current_phase = phase
        self.clear_animations()

        animations = None

        if phase == "entrance":
            animations = self.entrance_animations
        elif phase == "idle":
            animations = self.idle_animations
        elif phase == "exit":
            animations = self.exit_animations
        elif phase in self._custom_phases:
            animations = self._custom_phases[phase]
        else:
            logger.warning(f"Unknown animation phase: '{phase}'")
            return

        for start_time, anim in animations:
            anim.reset()
            self.add_animation(anim, current_scene_time + start_time)

            if anim.target in self.children:
                anim.update(self.children[anim.target].state, 0.0)
                logger.debug(f"  Applied frame 0 of animation to '{anim.target}'")

        logger.debug(f"  Loaded {len(animations)} animations for phase '{phase}'")

    def _check_phase_complete(self, scene_time: float) -> bool:
        """Check if all animations in current phase are complete."""
        if not self.current_animations:
            return True

        for start_time, anim in self.current_animations:
            if scene_time >= start_time:
                if not anim.completed:
                    return False

        max_start_time = max(start_time for start_time, _ in self.current_animations)
        if scene_time < max_start_time:
            return False

        return True

    async def await_phase_complete(
        self,
        phase: Optional[str] = None,
        timeout: Optional[float] = None,
        poll_interval: float = 0.1,
        wait_one_cycle: bool = False,
    ) -> bool:
        """Wait for the current animation phase to complete."""
        from .animation import Loop

        start_wait = time.time()

        one_cycle_duration = None
        if wait_one_cycle:
            for start_time, anim in self.current_animations:
                if isinstance(anim, Loop):
                    if hasattr(anim, "animation") and hasattr(anim.animation, "duration"):
                        one_cycle_duration = anim.animation.duration
                        logger.debug(
                            f"Detected Loop animation with cycle duration: {one_cycle_duration:.2f}s"
                        )
                        break

        while True:
            if phase is not None and self._current_phase != phase:
                if timeout and (time.time() - start_wait) >= timeout:
                    logger.warning(
                        f"Timeout waiting for phase '{phase}' (current: '{self._current_phase}')"
                    )
                    return False
                await asyncio.sleep(poll_interval)
                continue

            if wait_one_cycle and one_cycle_duration:
                elapsed = time.time() - start_wait
                if elapsed >= one_cycle_duration:
                    logger.debug(
                        f"One cycle of phase '{self._current_phase}' complete after {elapsed:.3f}s"
                    )
                    return True

            scene_time = self._time if hasattr(self, "_time") else 0.0
            if self._check_phase_complete(scene_time):
                logger.debug(
                    f"Phase '{self._current_phase}' complete after {time.time() - start_wait:.3f}s"
                )
                return True

            if timeout and (time.time() - start_wait) >= timeout:
                logger.warning(f"Timeout waiting for phase '{self._current_phase}' to complete")
                return False

            await asyncio.sleep(poll_interval)

    def on_enter(self):
        """Called when scene becomes active. Starts entrance phase."""
        logger.debug("Scene.on_enter() called")
        self.set_animation_phase("entrance")

    def on_exit(self, current_scene_time: Optional[float] = None):
        """Called when scene is deactivated. Starts exit phase."""
        logger.debug("Scene.on_exit() called")
        self.set_animation_phase("exit")

    def set_display_callback(self, callback: Callable[[RenderBuffer], None]):
        """Set callback function to display rendered buffer."""
        self._display_callback = callback

    def set_fps(self, fps: int):
        """Set target frames per second for standalone mode."""
        self._fps = fps

    async def start_async(self, duration: Optional[float] = None):
        """Start the render loop (async, standalone mode)."""
        self._running = True
        self._time = 0.0
        start_time = time.time()

        if self._scene_start_time is None:
            self._scene_start_time = start_time

        self.on_enter()

        frame_duration = 1.0 / self._fps

        try:
            frame_count = 0
            while self._running:
                frame_start = time.time()
                frame_count += 1

                self._time = time.time() - start_time
                scene_time = self._time - (
                    self._scene_start_time - start_time if self._scene_start_time else 0
                )

                if self._current_phase == "entrance" and self._check_phase_complete(scene_time):
                    if self.idle_animations:
                        logger.debug(f"Entrance phase complete, transitioning to idle")
                        self.set_animation_phase("idle")
                    else:
                        logger.debug(
                            f"Entrance phase complete, no idle animations - clearing phase"
                        )
                        self.set_animation_phase(None)
                elif self._current_phase == "idle" and self._check_phase_complete(scene_time):
                    logger.debug(f"Idle phase complete, restarting idle")
                    self.set_animation_phase("idle")

                buffer = self.render(self._time)

                if self._display_callback:
                    self._display_callback(buffer)

                if frame_count % 30 == 0 or self._current_phase == "exit":
                    logger.info(
                        f"Render loop: frame {frame_count}, phase={self._current_phase}, time={self._time:.3f}"
                    )

                if duration and self._time >= duration:
                    break

                frame_elapsed = time.time() - frame_start
                sleep_time = max(0, frame_duration - frame_elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            pass
        finally:
            self._running = False

    def stop(self):
        """Stop the render loop."""
        self._running = False

    def start(self, duration: Optional[float] = None):
        """Start the render loop (synchronous wrapper)."""
        asyncio.run(self.start_async(duration))

    async def __aenter__(self):
        """Async context manager entry - starts the render loop."""
        logger.info("Scene.__aenter__() called - starting render loop")
        self._render_task = asyncio.create_task(self.start_async())
        await asyncio.sleep(0.01)
        logger.info("Scene.__aenter__() complete - render loop started")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - runs exit animations and stops."""
        logger.info("Scene.__aexit__() called - starting exit sequence")

        self.on_exit()

        if self.exit_animations:
            max_duration = max(
                (start_time + anim.duration) for start_time, anim in self.exit_animations
            )
            logger.info(f"Waiting {max_duration:.3f}s for exit animations to complete")
            await asyncio.sleep(max_duration)
            logger.info(f"Exit animations wait complete")

        logger.info("Stopping render loop")
        self.stop()
        await self._render_task
        logger.info("Scene.__aexit__() complete - render loop stopped")
        return False

    def apply_all(self, animation_type, **kwargs):
        """Apply an animation to all children in the scene."""
        from .animation import slide_in_all, slide_out_all, fade_in_all, fade_out_all

        if isinstance(animation_type, str):
            type_map = {
                "slide_in": slide_in_all,
                "slide_out": slide_out_all,
                "fade_in": fade_in_all,
                "fade_out": fade_out_all,
            }
            if animation_type not in type_map:
                raise ValueError(
                    f"Unknown animation type: {animation_type}. Use: {list(type_map.keys())}"
                )
            animation_helper = type_map[animation_type]
        else:
            animation_helper = animation_type

        return animation_helper(list(self.children.keys()), **kwargs)

    def debug_state(self, log_to_file: bool = True, print_to_console: bool = True) -> str:
        """Generate debug output showing all component positions, dimensions, and animation states."""
        scene_time = self._time if hasattr(self, "_time") else 0.0

        lines = []
        lines.append("=" * 80)
        lines.append(f"SCENE DEBUG STATE (time={scene_time:.3f}s)")
        lines.append("=" * 80)
        lines.append(f"Scene dimensions: {self._width}x{self._height}")
        lines.append(f"Current phase: {self._current_phase}")
        lines.append(f"Active animations: {len(self.current_animations)}")
        lines.append(f"Focused child: {self._focused_child}")
        lines.append("")

        sorted_children = sorted(
            self.children.items(), key=lambda item: item[1].state.get("z_index", 0)
        )

        for child_id, instance in sorted_children:
            lines.append(f"Component: '{child_id}'")
            lines.append(f"  Type: {type(instance.component).__name__}")
            lines.append(f"  Dimensions: {instance.component.width}x{instance.component.height}")

            x = instance.state.get("x", 0)
            y = instance.state.get("y", 0)
            lines.append(f"  Position: x={x}, y={y}")

            in_bounds_x = 0 <= x < self._width
            in_bounds_y = 0 <= y < self._height
            fully_visible = (
                0 <= x
                and x + instance.component.width <= self._width
                and 0 <= y
                and y + instance.component.height <= self._height
            )

            if fully_visible:
                visibility = "FULLY VISIBLE"
            elif (
                in_bounds_x
                or in_bounds_y
                or (x + instance.component.width > 0 and y + instance.component.height > 0)
            ):
                visibility = "PARTIALLY VISIBLE"
            else:
                visibility = "OFF CANVAS"
            lines.append(f"  Visibility: {visibility}")

            lines.append(f"  Opacity: {instance.state.get('opacity', 1.0)}")
            lines.append(f"  Z-index: {instance.state.get('z_index', 0)}")
            lines.append(f"  Focused: {instance.component.focused}")
            lines.append(f"  Focusable: {instance.component.is_focusable()}")

            active_anims = [
                (start_time, anim)
                for start_time, anim in self.current_animations
                if anim.target == child_id
            ]

            if active_anims:
                lines.append(f"  Active animations: {len(active_anims)}")
                for start_time, anim in active_anims:
                    elapsed = max(0.0, scene_time - start_time)
                    progress = min(1.0, elapsed / anim.duration) if anim.duration > 0 else 1.0
                    lines.append(
                        f"    - {type(anim).__name__}: progress={progress:.2%}, "
                        f"elapsed={elapsed:.3f}s/{anim.duration:.3f}s, "
                        f"completed={anim.completed}"
                    )

                    if hasattr(anim, "to_params_int"):
                        lines.append(f"      Animating (int): {anim.to_params_int}")
                    if hasattr(anim, "to_params_float"):
                        lines.append(f"      Animating (float): {anim.to_params_float}")
            else:
                lines.append(f"  Active animations: None")

            lines.append("")

        output = "\n".join(lines)

        if log_to_file:
            for line in lines:
                logger.info(line)

        if print_to_console:
            print(output)

        return output
