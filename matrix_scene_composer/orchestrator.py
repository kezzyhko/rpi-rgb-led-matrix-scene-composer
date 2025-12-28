"""Orchestrator - Top-level controller managing scenes and render loop."""

import asyncio
import time
from typing import Dict, Optional, Callable
from .scene import Scene
from .render_buffer import RenderBuffer
from .component import DEBUG


class Orchestrator:
    """Top-level controller managing the render loop and scenes."""

    def __init__(self, width: int, height: int, fps: int = 30):
        """
        Initialize orchestrator.

        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
            fps: Target frames per second
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_duration = 1.0 / fps

        self.scenes: Dict[str, Scene] = {}
        self.current_scene: Optional[Scene] = None
        self.current_scene_id: Optional[str] = None

        self.time = 0.0  # Global clock in seconds
        self.running = False

        # Optional display callback
        self._display_callback: Optional[Callable[[RenderBuffer], None]] = None

    def set_display_callback(self, callback: Callable[[RenderBuffer], None]):
        """
        Set callback function to display rendered buffer.

        Args:
            callback: Function that takes RenderBuffer and displays it
        """
        self._display_callback = callback

    def add_scene(self, scene_id: str, scene: Scene):
        """
        Add a scene to the orchestrator.

        Args:
            scene_id: Unique identifier for the scene
            scene: Scene instance
        """
        self.scenes[scene_id] = scene

    def transition_to(self, scene_id: str):
        """
        Transition to a scene.
        For now, just switches immediately (no transition animation).

        Args:
            scene_id: ID of scene to switch to
        """
        if scene_id not in self.scenes:
            raise ValueError(f"Scene '{scene_id}' not found")

        # Call exit on current scene if exists
        if self.current_scene:
            self.current_scene.on_exit()

        # Switch to new scene
        self.current_scene = self.scenes[scene_id]
        self.current_scene_id = scene_id

        # Call enter on new scene
        self.current_scene.on_enter()

    def _render_frame(self) -> RenderBuffer:
        """
        Render a single frame.

        Returns:
            RenderBuffer with rendered frame
        """
        if DEBUG:
            print(f"\n[FRAME] Orchestrator._render_frame() at time={self.time:.2f}")

        if not self.current_scene:
            # Return empty buffer if no scene
            return RenderBuffer(self.width, self.height)

        # Update scene's internal time
        self.current_scene._time = self.time

        # Check for phase transitions (same logic as Scene.start_async)
        scene = self.current_scene
        scene_time = scene._time

        if scene._current_phase == 'entrance' and scene._check_phase_complete(scene_time):
            if scene.idle_animations:
                scene.set_animation_phase('idle')
            else:
                scene.set_animation_phase(None)
        elif scene._current_phase == 'idle' and scene._check_phase_complete(scene_time):
            scene.set_animation_phase('idle')

        # Render current scene
        buffer = self.current_scene.render(self.time)

        if DEBUG:
            print(f"[FRAME COMPLETE]\n")

        return buffer

    async def start_async(self, duration: Optional[float] = None):
        """
        Start the render loop (async).

        Args:
            duration: Optional duration in seconds. If None, runs indefinitely.

        Usage:
            async with orchestrator:
                await orchestrator.start()

            Or:
                asyncio.run(orchestrator.start())
        """
        self.running = True
        self.time = 0.0
        start_time = time.time()

        try:
            while self.running:
                frame_start = time.time()

                # Render frame
                buffer = self._render_frame()

                # Display via callback if set
                if self._display_callback:
                    self._display_callback(buffer)

                # Update global time
                self.time = time.time() - start_time

                # Check duration
                if duration and self.time >= duration:
                    break

                # Sleep to maintain target FPS (async)
                frame_elapsed = time.time() - frame_start
                sleep_time = max(0, self.frame_duration - frame_elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            # Handle cancellation gracefully
            pass
        finally:
            self.running = False

    def stop(self):
        """Stop the render loop."""
        self.running = False

    def start(self, duration: Optional[float] = None):
        """
        Start the render loop (synchronous wrapper).

        Args:
            duration: Optional duration in seconds. If None, runs indefinitely.

        Usage:
            # Synchronous (blocks until stopped):
            orch.start()

            # Async (use start_async instead):
            await orch.start_async()
        """
        asyncio.run(self.start_async(duration))

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - stops the orchestrator."""
        self.stop()
        return False

    def render_single_frame(self, time_value: float) -> RenderBuffer:
        """
        Render a single frame at specific time without starting loop.
        Useful for testing.

        Args:
            time_value: Time value to render at

        Returns:
            RenderBuffer with rendered frame
        """
        self.time = time_value
        return self._render_frame()
