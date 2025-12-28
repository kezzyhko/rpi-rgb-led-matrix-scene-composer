"""Scene - Composite component container with positioning, layering, and animations."""

import asyncio
import time
import logging
from typing import Dict, Tuple, Optional, List, Callable
from .component import Component, cache_with_dict, DEBUG
from .render_buffer import RenderBuffer

# Setup logging to file
logging.basicConfig(
    filename='/tmp/animation_demo.log',
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d - %(message)s',
    datefmt='%H:%M:%S'
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
    """

    def __init__(self, width: int = None, height: int = None, size: Tuple[int, int] = None,
                 entrance_animations: Optional[List] = None,
                 idle_animations: Optional[List] = None,
                 exit_animations: Optional[List] = None):
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
        super().__init__()  # Initialize Component base class

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

        # Animation phases - built-in phases
        self.entrance_animations = entrance_animations or []
        self.idle_animations = idle_animations or []
        self.exit_animations = exit_animations or []

        # Custom animation phases - user-defined
        self._custom_phases: Dict[str, List[Tuple[float, 'Animation']]] = {}

        # Current active animations
        self.current_animations: List[Tuple[float, 'Animation']] = []
        self._scene_start_time: Optional[float] = None
        self._current_phase: Optional[str] = None  # Current phase name (built-in or custom)

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
        **state
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
        # Support position=(x, y) tuple format
        if position is not None:
            state['x'] = position[0]
            state['y'] = position[1]

        self.children[child_id] = ComponentInstance(component, **state)

    def remove_child(self, child_id: str):
        """Remove child component from scene."""
        if child_id in self.children:
            del self.children[child_id]

    def add_animation(self, animation: 'Animation', start_time: float = 0.0):
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
        # Use self._time (elapsed since render loop start) instead of parameter time
        scene_time = self._time if hasattr(self, '_time') else 0.0

        child_states = {}

        for child_id, instance in self.children.items():
            # Apply animations using the Animation's own update() method
            for start_time, anim in self.current_animations:
                if anim.target == child_id:
                    # Always render animation, even if delayed (elapsed will be clamped to 0)
                    # This ensures the first frame is rendered immediately
                    elapsed = max(0.0, scene_time - start_time)

                    # Update animation with elapsed time
                    anim.update(instance.state, elapsed)

            # Build state dict for rendering (includes child component state for cache invalidation)
            state = instance.state.copy()
            child_component_state = instance.component.compute_state(time)
            from .component import _make_hashable
            state['_child_state'] = _make_hashable(child_component_state)

            child_states[child_id] = state

        # No 'time' key! Time passed separately to avoid cache invalidation
        return {'children': child_states}

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
            state['children'].items(),
            key=lambda item: item[1].get('z_index', 0)
        )

        # Composite children
        for child_id, child_state in sorted_children:
            instance = self.children[child_id]

            # Child renders itself (uses its own cache)
            buffer = instance.component.render(time)

            # Composite with child's state
            # Always use x and y (convert to ints for pixel positions)
            x = int(child_state.get('x', 0))
            y = int(child_state.get('y', 0))

            canvas.blit(
                buffer,
                (x, y),
                child_state.get('opacity', 1.0)
            )

        return canvas

    def register_animation_phase(self, phase_name: str, animations: List[Tuple[float, 'Animation']]):
        """
        Register a custom animation phase.

        Args:
            phase_name: Name of the phase (e.g., 'shake', 'bounce', 'pulse')
            animations: List of (start_time, Animation) tuples

        Example:
            scene.register_animation_phase('shake', [
                (0.0, Animate("logo", to_params_int={'x': 5}, duration=0.1)),
                (0.1, Animate("logo", to_params_int={'x': -5}, duration=0.1)),
                (0.2, Animate("logo", to_params_int={'x': 0}, duration=0.1)),
            ])
        """
        self._custom_phases[phase_name] = animations
        logger.info(f"Registered custom animation phase '{phase_name}' with {len(animations)} animation(s)")

    def set_animation_phase(self, phase: Optional[str]):
        """
        Set the current animation phase (thread-safe, user-facing API).

        Args:
            phase: Phase name ('entrance', 'idle', 'exit', custom phase name, or None)
                  - None: Clear all animations
                  - 'entrance', 'idle', 'exit': Built-in phases
                  - Custom string: User-registered phase via register_animation_phase()

        Example:
            scene.set_animation_phase('shake')      # Start shake animation
            scene.set_animation_phase('idle')       # Return to idle
            scene.set_animation_phase(None)         # Stop all animations
        """
        current_scene_time = self._time if hasattr(self, '_time') else 0.0

        if phase is None:
            # Clear all animations
            logger.debug(f"set_animation_phase(None) - clearing all animations")
            self._current_phase = None
            self.clear_animations()
        else:
            # Start the specified phase
            logger.debug(f"set_animation_phase('{phase}') at scene_time={current_scene_time:.3f}")
            self._start_phase(phase, current_scene_time)

    def _start_phase(self, phase: str, current_scene_time: float = 0.0):
        """Internal method to start an animation phase (called by set_animation_phase)."""
        self._current_phase = phase
        self.clear_animations()

        # Load animations for this phase, offsetting by current scene time
        animations = None

        # Check built-in phases first
        if phase == 'entrance':
            animations = self.entrance_animations
        elif phase == 'idle':
            animations = self.idle_animations
        elif phase == 'exit':
            animations = self.exit_animations
        # Then check custom phases
        elif phase in self._custom_phases:
            animations = self._custom_phases[phase]
        else:
            logger.warning(f"Unknown animation phase: '{phase}'")
            return

        # Load animations with time offset
        # Reset each animation before adding it so it re-resolves from current position
        for start_time, anim in animations:
            anim.reset()  # Clear cached resolved values
            self.add_animation(anim, current_scene_time + start_time)

            # Immediately apply frame 0 of the animation to ensure component starts at correct position
            # This prevents the component from being visible at its base position before animation starts
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

    async def await_phase_complete(self, phase: Optional[str] = None, timeout: Optional[float] = None, poll_interval: float = 0.1, wait_one_cycle: bool = False) -> bool:
        """
        Wait for the current animation phase (or specific phase) to complete.

        Args:
            phase: Specific phase to wait for (or None to wait for current phase)
            timeout: Maximum time to wait in seconds (or None for no timeout)
            poll_interval: How often to check phase completion (default 0.1s)
            wait_one_cycle: If True and phase contains Loop animations, wait for one cycle
                           to complete instead of waiting forever (default False)

        Returns:
            True if phase completed, False if timeout reached

        Example:
            # Wait for idle animations to complete
            scene.set_animation_phase('idle')
            await scene.await_phase_complete()

            # Wait for looping idle animation to complete one cycle
            await scene.await_phase_complete('idle', wait_one_cycle=True)

            # Wait for specific phase with timeout
            scene.set_animation_phase('custom')
            completed = await scene.await_phase_complete('custom', timeout=5.0)
        """
        from .animation import Loop
        start_wait = time.time()

        # If wait_one_cycle is True, calculate the duration of one cycle for Loop animations
        one_cycle_duration = None
        if wait_one_cycle:
            for start_time, anim in self.current_animations:
                if isinstance(anim, Loop):
                    # Loop contains a child animation, get its duration
                    if hasattr(anim, 'animation') and hasattr(anim.animation, 'duration'):
                        one_cycle_duration = anim.animation.duration
                        logger.debug(f"Detected Loop animation with cycle duration: {one_cycle_duration:.2f}s")
                        break

        while True:
            # Check if we're waiting for a specific phase or current phase
            if phase is not None and self._current_phase != phase:
                # Not in the phase we're waiting for
                if timeout and (time.time() - start_wait) >= timeout:
                    logger.warning(f"Timeout waiting for phase '{phase}' (current: '{self._current_phase}')")
                    return False
                await asyncio.sleep(poll_interval)
                continue

            # If we're waiting for one cycle and we know the duration, check if elapsed
            if wait_one_cycle and one_cycle_duration:
                elapsed = time.time() - start_wait
                if elapsed >= one_cycle_duration:
                    logger.debug(f"One cycle of phase '{self._current_phase}' complete after {elapsed:.3f}s")
                    return True

            # Check if phase is complete (for non-looping animations)
            scene_time = self._time if hasattr(self, '_time') else 0.0
            if self._check_phase_complete(scene_time):
                logger.debug(f"Phase '{self._current_phase}' complete after {time.time() - start_wait:.3f}s")
                return True

            # Check timeout
            if timeout and (time.time() - start_wait) >= timeout:
                logger.warning(f"Timeout waiting for phase '{self._current_phase}' to complete")
                return False

            # Wait before checking again
            await asyncio.sleep(poll_interval)

    # Rest of Scene methods remain the same for now (on_enter, on_exit, etc.)
    def on_enter(self):
        """Called when scene becomes active. Starts entrance phase."""
        logger.debug("Scene.on_enter() called")
        self.set_animation_phase('entrance')

    def on_exit(self, current_scene_time: Optional[float] = None):
        """Called when scene is deactivated. Starts exit phase."""
        logger.debug("Scene.on_exit() called")
        self.set_animation_phase('exit')

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

        # Initialize scene start time
        if self._scene_start_time is None:
            self._scene_start_time = start_time

        # Start entrance animations
        self.on_enter()

        frame_duration = 1.0 / self._fps

        try:
            frame_count = 0
            while self._running:
                frame_start = time.time()
                frame_count += 1

                # Calculate scene time
                self._time = time.time() - start_time
                scene_time = self._time - (self._scene_start_time - start_time if self._scene_start_time else 0)

                # Check phase transitions
                if self._current_phase == 'entrance' and self._check_phase_complete(scene_time):
                    if self.idle_animations:
                        logger.debug(f"Entrance phase complete, transitioning to idle")
                        self.set_animation_phase('idle')
                    else:
                        logger.debug(f"Entrance phase complete, no idle animations - clearing phase")
                        self.set_animation_phase(None)
                elif self._current_phase == 'idle' and self._check_phase_complete(scene_time):
                    logger.debug(f"Idle phase complete, restarting idle")
                    self.set_animation_phase('idle')

                # Render frame
                buffer = self.render(self._time)

                # Display via callback if set
                if self._display_callback:
                    self._display_callback(buffer)

                # Log periodically
                if frame_count % 30 == 0 or self._current_phase == 'exit':
                    logger.info(f"Render loop: frame {frame_count}, phase={self._current_phase}, time={self._time:.3f}")

                # Check duration
                if duration and self._time >= duration:
                    break

                # Sleep to maintain target FPS
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
            max_duration = max((start_time + anim.duration) for start_time, anim in self.exit_animations)
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
                'slide_in': slide_in_all,
                'slide_out': slide_out_all,
                'fade_in': fade_in_all,
                'fade_out': fade_out_all,
            }
            if animation_type not in type_map:
                raise ValueError(f"Unknown animation type: {animation_type}. Use: {list(type_map.keys())}")
            animation_helper = type_map[animation_type]
        else:
            animation_helper = animation_type

        return animation_helper(list(self.children.keys()), **kwargs)

    def debug_state(self, log_to_file: bool = True, print_to_console: bool = True) -> str:
        """
        Generate debug output showing all component positions, dimensions, and animation states.

        Args:
            log_to_file: If True, log to the configured logger
            print_to_console: If True, print to stdout

        Returns:
            Debug output string
        """
        scene_time = self._time if hasattr(self, '_time') else 0.0

        lines = []
        lines.append("=" * 80)
        lines.append(f"SCENE DEBUG STATE (time={scene_time:.3f}s)")
        lines.append("=" * 80)
        lines.append(f"Scene dimensions: {self._width}x{self._height}")
        lines.append(f"Current phase: {self._current_phase}")
        lines.append(f"Active animations: {len(self.current_animations)}")
        lines.append("")

        # Show all children sorted by z_index
        sorted_children = sorted(
            self.children.items(),
            key=lambda item: item[1].state.get('z_index', 0)
        )

        for child_id, instance in sorted_children:
            lines.append(f"Component: '{child_id}'")
            lines.append(f"  Type: {type(instance.component).__name__}")
            lines.append(f"  Dimensions: {instance.component.width}x{instance.component.height}")

            # Position
            x = instance.state.get('x', 0)
            y = instance.state.get('y', 0)
            lines.append(f"  Position: x={x}, y={y}")

            # Check if within canvas bounds
            in_bounds_x = 0 <= x < self._width
            in_bounds_y = 0 <= y < self._height
            fully_visible = (0 <= x and
                           x + instance.component.width <= self._width and
                           0 <= y and
                           y + instance.component.height <= self._height)

            if fully_visible:
                visibility = "FULLY VISIBLE"
            elif in_bounds_x or in_bounds_y or (x + instance.component.width > 0 and y + instance.component.height > 0):
                visibility = "PARTIALLY VISIBLE"
            else:
                visibility = "OFF CANVAS"
            lines.append(f"  Visibility: {visibility}")

            # Other state
            lines.append(f"  Opacity: {instance.state.get('opacity', 1.0)}")
            lines.append(f"  Z-index: {instance.state.get('z_index', 0)}")

            # Check for active animations targeting this component
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
                    lines.append(f"    - {type(anim).__name__}: progress={progress:.2%}, "
                               f"elapsed={elapsed:.3f}s/{anim.duration:.3f}s, "
                               f"completed={anim.completed}")

                    # Show what's being animated
                    if hasattr(anim, 'to_params_int'):
                        lines.append(f"      Animating (int): {anim.to_params_int}")
                    if hasattr(anim, 'to_params_float'):
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
