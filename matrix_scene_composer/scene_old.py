"""Scene - Container for components with positioning and layering."""

import asyncio
import time
import logging
from typing import Dict, Tuple, Optional, List, Callable
from .component import Component, DEBUG
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
    """Wrapper for component with positioning and rendering properties."""

    def __init__(self, component: Component, position: Tuple[int, int], z_index: int, opacity: float):
        self.component = component
        self.position = position
        self.z_index = z_index
        self.opacity = opacity


class Scene:
    """Container for components with fixed canvas size."""

    def __init__(self, size=None, width: int = None, height: int = None,
                 entrance_animations: Optional[List] = None,
                 idle_animations: Optional[List] = None,
                 exit_animations: Optional[List] = None):
        """
        Initialize scene.

        Args:
            size: Tuple of (width, height) - convenient when using display.size
            width: Scene canvas width (if size not provided)
            height: Scene canvas height (if size not provided)
            entrance_animations: List of (start_time, animation) tuples to run when scene enters.
                                Example: [(0.0, Anim1), (2.0, Anim2), (3.5, Anim3)]
            idle_animations: List of (start_time, animation) tuples for continuous animations
            exit_animations: List of (start_time, animation) tuples to run when scene exits
        """
        if size is not None:
            self.width, self.height = size
        elif width is not None and height is not None:
            self.width = width
            self.height = height
        else:
            raise ValueError("Must provide either 'size' or both 'width' and 'height'")

        self.components: Dict[str, ComponentInstance] = {}
        self.canvas = RenderBuffer(self.width, self.height)

        # Animation phases
        self.entrance_animations = entrance_animations or []
        self.idle_animations = idle_animations or []
        self.exit_animations = exit_animations or []

        # Current active animations
        self.current_animations: List[Tuple[float, 'Animation']] = []
        self._scene_start_time: Optional[float] = None
        self._current_phase: Optional[str] = None  # 'entrance', 'idle', or 'exit'

        # Standalone mode (without orchestrator)
        self._display_callback: Optional[Callable[[RenderBuffer], None]] = None
        self._running = False
        self._time = 0.0
        self._fps = 30

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

    def add_animation(self, animation: 'Animation', start_time: float = 0.0):
        """
        Add animation to current animations.

        Args:
            animation: Animation instance to add
            start_time: Time relative to scene start when animation should begin
        """
        self.current_animations.append((start_time, animation))

    def clear_animations(self):
        """Clear all current animations."""
        self.current_animations.clear()

    def _start_phase(self, phase: str, current_scene_time: float = 0.0):
        """
        Start a new animation phase.

        Args:
            phase: 'entrance', 'idle', or 'exit'
            current_scene_time: Current scene time (for scheduling animations relative to now)
        """
        logger.info(f"Scene._start_phase('{phase}') called at scene_time={current_scene_time:.3f}")
        self._current_phase = phase
        self.clear_animations()
        # DO NOT reset _scene_start_time - scene time should be monotonic!
        # Animations track their own start times relative to the scene clock.

        # Load animations for this phase, offsetting by current scene time
        # so they start NOW rather than at scene_time=0
        if phase == 'entrance':
            for start_time, anim in self.entrance_animations:
                self.add_animation(anim, current_scene_time + start_time)
            logger.info(f"  Loaded {len(self.entrance_animations)} entrance animations")
        elif phase == 'idle':
            for start_time, anim in self.idle_animations:
                self.add_animation(anim, current_scene_time + start_time)
            logger.info(f"  Loaded {len(self.idle_animations)} idle animations")
        elif phase == 'exit':
            for start_time, anim in self.exit_animations:
                self.add_animation(anim, current_scene_time + start_time)
            logger.info(f"  Loaded {len(self.exit_animations)} exit animations")

    def _check_phase_complete(self, scene_time: float) -> bool:
        """
        Check if all animations in current phase are complete.

        Args:
            scene_time: Current time relative to scene start

        Returns:
            True if all animations are done
        """
        if not self.current_animations:
            return True

        # Check if all animations that should have started are completed
        for start_time, anim in self.current_animations:
            # Only check animations that have reached their start time
            if scene_time >= start_time:
                if not anim.completed:
                    return False

        # Also check if all animations have at least started
        # (scene_time must be past the last animation's start time)
        max_start_time = max(start_time for start_time, _ in self.current_animations)
        if scene_time < max_start_time:
            return False

        return True

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

        # Initialize scene start time if not set
        if self._scene_start_time is None:
            self._scene_start_time = time

        scene_time = time - self._scene_start_time

        # Update animations (modifies ComponentInstance properties)
        for start_time, anim in self.current_animations[:]:  # Copy list since we may remove
            # Check if animation target exists
            if anim.target not in self.components:
                continue

            instance = self.components[anim.target]

            # Calculate when this animation should actually start (global time)
            anim_start_time = self._scene_start_time + start_time

            # Always call update, but pass the animation's start time if we haven't reached it yet
            # This ensures from_params are applied at progress=0
            if scene_time < start_time:
                # Call update with the animation's start time (elapsed will be 0)
                anim.update(instance, anim_start_time)
            else:
                # Update animation with current time
                if anim.update(instance, time):
                    # Animation completed - remove it
                    self.current_animations.remove((start_time, anim))

        # Check if current phase is complete and transition to next phase
        if self._current_phase == 'entrance' and self._check_phase_complete(scene_time):
            if self.idle_animations:
                logger.info(f"Entrance phase complete at scene_time={scene_time:.3f}, transitioning to idle")
                self._start_phase('idle', scene_time)
        elif self._current_phase == 'idle' and self._check_phase_complete(scene_time):
            # Idle phase complete - restart idle animations (loop forever)
            logger.info(f"Idle phase complete at scene_time={scene_time:.3f}, restarting idle")
            self._start_phase('idle', scene_time)

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

    def apply_all(self, animation_type, **kwargs):
        """
        Apply an animation to all components in the scene.

        Args:
            animation_type: Either a string ('slide_in', 'slide_out', 'fade_in', 'fade_out')
                           or an animation helper function for backward compatibility
            **kwargs: Additional arguments (duration, easing, etc.)

        Returns:
            List of (start_time, Animation) tuples

        Example:
            scene.apply_all('slide_in')
            scene.apply_all('slide_out', duration=2.0)
            scene.apply_all('fade_in', start_time=0.5, duration=1.5)
        """
        from .animation import slide_in_all, slide_out_all, fade_in_all, fade_out_all

        # Support string types
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
            # Backward compatibility: support passing function directly
            animation_helper = animation_type

        return animation_helper(list(self.components.keys()), **kwargs)

    def on_enter(self):
        """Called when scene becomes active. Starts entrance phase."""
        logger.info("Scene.on_enter() called")
        self._start_phase('entrance')

    def on_exit(self, current_scene_time: Optional[float] = None):
        """
        Called when scene is deactivated. Starts exit phase.

        Args:
            current_scene_time: Current scene time (if None, will be calculated)
        """
        if current_scene_time is None:
            # Calculate from current _time if available
            if self._scene_start_time is not None and hasattr(self, '_time'):
                current_scene_time = self._time
            else:
                current_scene_time = 0.0

        logger.info(f"Scene.on_exit() called at scene_time={current_scene_time:.3f}")
        self._start_phase('exit', current_scene_time)

    def set_display_callback(self, callback: Callable[[RenderBuffer], None]):
        """
        Set callback function to display rendered buffer.

        Args:
            callback: Function that takes RenderBuffer and displays it
        """
        self._display_callback = callback

    def set_fps(self, fps: int):
        """Set target frames per second for standalone mode."""
        self._fps = fps

    async def start_async(self, duration: Optional[float] = None):
        """
        Start the render loop (async, standalone mode).

        Args:
            duration: Optional duration in seconds. If None, runs indefinitely.
        """
        self._running = True
        self._time = 0.0
        start_time = time.time()

        # Start entrance animations
        self.on_enter()

        frame_duration = 1.0 / self._fps

        try:
            frame_count = 0
            while self._running:
                frame_start = time.time()
                frame_count += 1

                # Render frame
                buffer = self.render(self._time)

                # Display via callback if set
                if self._display_callback:
                    self._display_callback(buffer)

                # Log every 30 frames (once per second at 30fps) and during exit phase
                if frame_count % 30 == 0 or self._current_phase == 'exit':
                    logger.info(f"Render loop: frame {frame_count}, phase={self._current_phase}, time={self._time:.3f}")

                # Update time
                self._time = time.time() - start_time

                # Check duration
                if duration and self._time >= duration:
                    break

                # Sleep to maintain target FPS (async)
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
        """
        Start the render loop (synchronous wrapper).

        Args:
            duration: Optional duration in seconds. If None, runs indefinitely.
        """
        asyncio.run(self.start_async(duration))

    async def __aenter__(self):
        """Async context manager entry - starts the render loop."""
        logger.info("Scene.__aenter__() called - starting render loop")
        # Start the scene task in the background
        self._render_task = asyncio.create_task(self.start_async())
        # Give it a moment to start
        await asyncio.sleep(0.01)
        logger.info("Scene.__aenter__() complete - render loop started")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - runs exit animations and stops."""
        logger.info("Scene.__aexit__() called - starting exit sequence")

        # Trigger exit animations (loads exit animations into current_animations)
        self.on_exit()

        # Wait for exit animations to complete (get max duration)
        # IMPORTANT: The render loop must keep running during this time!
        # We cannot call stop() yet because that would stop rendering frames.
        if self.exit_animations:
            max_duration = max((start_time + anim.duration) for start_time, anim in self.exit_animations)
            logger.info(f"Waiting {max_duration:.3f}s for exit animations to complete")
            # Sleep while the render loop continues to run and show exit animations
            await asyncio.sleep(max_duration)
            logger.info(f"Exit animations wait complete")

        # NOW stop the scene after animations have been displayed
        logger.info("Stopping render loop")
        self.stop()
        await self._render_task
        logger.info("Scene.__aexit__() complete - render loop stopped")
        return False
