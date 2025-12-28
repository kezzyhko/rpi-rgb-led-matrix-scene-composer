"""Animation framework for animating component instance properties."""

import math
from typing import Optional, List, Dict, Any, Callable


# Easing functions
def ease_linear(t: float) -> float:
    """Linear easing (no acceleration)."""
    return t


def ease_in_quad(t: float) -> float:
    """Quadratic ease-in (accelerating from zero)."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out (decelerating to zero)."""
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out (acceleration until halfway, then deceleration)."""
    return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t


def ease_in_cubic(t: float) -> float:
    """Cubic ease-in."""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out."""
    return (t - 1) ** 3 + 1


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out."""
    return 4 * t * t * t if t < 0.5 else (t - 1) * (2 * t - 2) ** 2 + 1


def ease_out_bounce(t: float) -> float:
    """Bounce ease-out."""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def ease_out_elastic(t: float) -> float:
    """Elastic ease-out."""
    if t == 0 or t == 1:
        return t
    return math.pow(2, -10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1


def ease_gravity(t: float) -> float:
    """
    Gravity-based easing simulating a projectile motion (inverted parabola).

    Uses physics: y(t) = v0*t - 0.5*g*t^2
    where g ≈ 9.82 m/s^2 (normalized for t in [0,1])

    For a projectile thrown upward:
    - At t=0: y=0 (ground level, start position)
    - At t=0.5: y=1 (peak height)
    - At t=1: y=0 (back to ground)

    The formula: y(t) = -4*(t-0.5)^2 + 1 creates an inverted parabola
    This is equivalent to: y(t) = 4*t*(1-t)

    Returns values from 0 (start) → 1 (peak) → 0 (end)
    Perfect for "jump up and land back" animations.
    """
    # Inverted parabola: 4*t*(1-t) = 4t - 4t^2
    return 4 * t * (1 - t)


# Easing function registry
EASING_FUNCTIONS: Dict[str, Callable[[float], float]] = {
    'linear': ease_linear,
    'ease_in': ease_in_quad,
    'ease_out': ease_out_quad,
    'ease_in_out': ease_in_out_quad,
    'ease_in_quad': ease_in_quad,
    'ease_out_quad': ease_out_quad,
    'ease_in_out_quad': ease_in_out_quad,
    'ease_in_cubic': ease_in_cubic,
    'ease_out_cubic': ease_out_cubic,
    'ease_in_out_cubic': ease_in_out_cubic,
    'bounce': ease_out_bounce,
    'elastic': ease_out_elastic,
    'gravity': ease_gravity,
}


class Animation:
    """
    Base class for animations.

    Animations modify ComponentInstance properties over time.
    """

    def __init__(self, target: str, duration: float, easing: str = 'linear'):
        """
        Initialize animation.

        Args:
            target: Component ID to animate
            duration: Animation duration in seconds
            easing: Easing function name
        """
        self.target = target
        self.duration = duration
        self.easing = easing
        self.completed = False

        if easing not in EASING_FUNCTIONS:
            raise ValueError(f"Unknown easing function: {easing}. Available: {list(EASING_FUNCTIONS.keys())}")

    def update(self, state: dict, elapsed: float) -> bool:
        """
        Update animation and apply to state.

        Args:
            state: State dict to modify
            elapsed: Time elapsed since animation started (in seconds)

        Returns:
            True if animation completed, False otherwise
        """
        if self.completed:
            return True

        if elapsed >= self.duration:
            # Animation complete - apply final state
            self._apply(state, 1.0)
            self.completed = True
            return True

        # Calculate progress with easing
        progress = elapsed / self.duration
        eased_progress = self._apply_easing(progress)

        # Apply animation at current progress
        self._apply(state, eased_progress)
        return False

    def _apply_easing(self, t: float) -> float:
        """Apply easing function to linear progress."""
        easing_fn = EASING_FUNCTIONS[self.easing]
        return easing_fn(t)

    def _apply(self, state: dict, progress: float):
        """
        Apply animation to state at given progress.

        Override in subclasses to implement animation behavior.

        Args:
            state: State dict to modify
            progress: Animation progress from 0.0 to 1.0 (eased)
        """
        raise NotImplementedError("Subclasses must implement _apply()")

    def reset(self):
        """Reset animation to initial state."""
        self.completed = False


class Animate(Animation):
    """
    Animate arbitrary ComponentInstance parameters.

    Example:
        # Absolute positioning
        Animate(
            target='logo',
            from_params={'x': -32, 'y': 4},
            to_params={'x': 16, 'y': 4},
            duration=1.0
        )

        # Relative positioning
        Animate(
            target='logo',
            from_params_rel={'x': -48},  # 48 pixels left of target
            to_params_rel={'x': 0},      # at target position
            duration=1.0
        )
    """

    def __init__(
        self,
        target: str,
        from_params: Optional[Dict[str, Any]] = None,
        from_params_rel: Optional[Dict[str, Any]] = None,
        to_params: Optional[Dict[str, Any]] = None,
        to_params_rel: Optional[Dict[str, Any]] = None,
        from_params_int: Optional[Dict[str, Any]] = None,
        from_params_rel_int: Optional[Dict[str, Any]] = None,
        to_params_int: Optional[Dict[str, Any]] = None,
        to_params_rel_int: Optional[Dict[str, Any]] = None,
        duration: float = 1.0,
        easing: str = 'linear'
    ):
        """
        Initialize parameter animation.

        Args:
            target: Component ID to animate
            from_params: Absolute starting parameters {'x': 10, 'y': 20, 'opacity': 0.5}
            from_params_rel: Relative starting parameters (offset from to_params)
            to_params: Absolute ending parameters
            to_params_rel: Relative ending parameters (offset from current position)
            from_params_int: Same as from_params but values are rounded to integers
            from_params_rel_int: Same as from_params_rel but values are rounded to integers
            to_params_int: Same as to_params but values are rounded to integers
            to_params_rel_int: Same as to_params_rel but values are rounded to integers
            duration: Animation duration in seconds
            easing: Easing function name
        """
        super().__init__(target, duration, easing)
        self.from_params = from_params or {}
        self.from_params_rel = from_params_rel or {}
        self.to_params = to_params or {}
        self.to_params_rel = to_params_rel or {}
        self.from_params_int = from_params_int or {}
        self.from_params_rel_int = from_params_rel_int or {}
        self.to_params_int = to_params_int or {}
        self.to_params_rel_int = to_params_rel_int or {}

        # Track which parameters should be rounded to integers
        self._int_params = set(
            list(self.from_params_int.keys()) +
            list(self.from_params_rel_int.keys()) +
            list(self.to_params_int.keys()) +
            list(self.to_params_rel_int.keys())
        )

        # Cache resolved start/end values (computed on first update)
        self._resolved_from: Optional[Dict[str, Any]] = None
        self._resolved_to: Optional[Dict[str, Any]] = None

    def reset(self):
        """Reset animation to initial state, clearing cached resolved parameters."""
        super().reset()
        self._resolved_from = None
        self._resolved_to = None

    def _resolve_params(self, state: dict):
        """Resolve relative parameters to absolute values."""
        if self._resolved_from is not None:
            return  # Already resolved

        self._resolved_from = {}
        self._resolved_to = {}

        # Get all parameters to animate (including _int variants)
        all_params = set(
            list(self.from_params.keys()) +
            list(self.from_params_rel.keys()) +
            list(self.to_params.keys()) +
            list(self.to_params_rel.keys()) +
            list(self.from_params_int.keys()) +
            list(self.from_params_rel_int.keys()) +
            list(self.to_params_int.keys()) +
            list(self.to_params_rel_int.keys())
        )

        for param in all_params:
            # Get current value from state
            # Generic: any parameter is looked up directly in state
            # Default to 0 if not present (allows animating new properties)
            current = state.get(param, 0)

            # Resolve 'to' value (check _int variants first)
            if param in self.to_params_int:
                to_val = self.to_params_int[param]
            elif param in self.to_params_rel_int:
                to_val = current + self.to_params_rel_int[param]
            elif param in self.to_params:
                to_val = self.to_params[param]
            elif param in self.to_params_rel:
                to_val = current + self.to_params_rel[param]
            else:
                to_val = current

            # Resolve 'from' value (check _int variants first)
            if param in self.from_params_int:
                from_val = self.from_params_int[param]
            elif param in self.from_params_rel_int:
                from_val = to_val + self.from_params_rel_int[param]
            elif param in self.from_params:
                from_val = self.from_params[param]
            elif param in self.from_params_rel:
                from_val = to_val + self.from_params_rel[param]
            else:
                from_val = current

            self._resolved_from[param] = from_val
            self._resolved_to[param] = to_val

    def _apply(self, state: dict, progress: float):
        """Apply parameter interpolation at given progress."""
        # Resolve parameters on first apply
        if self._resolved_from is None:
            self._resolve_params(state)

        # Interpolate each parameter
        for param in self._resolved_from:
            from_val = self._resolved_from[param]
            to_val = self._resolved_to[param]

            # Linear interpolation
            value = from_val + (to_val - from_val) * progress

            # Round to integer if this parameter was declared with _int variant
            if param in self._int_params:
                value = int(value)

            # Apply to state
            # Generic: set any parameter directly in state
            state[param] = value

    def reset(self):
        """Reset animation including cached parameter resolution."""
        super().reset()
        self._resolved_from = None
        self._resolved_to = None


class FadeIn(Animate):
    """
    Fade component in from transparent to opaque.

    Example:
        FadeIn(target='logo', duration=0.5)
        FadeIn(target='logo', from_opacity=0.0, to_opacity=0.8, duration=0.5)
    """

    def __init__(
        self,
        target: str,
        from_opacity: float = 0.0,
        to_opacity: float = 1.0,
        duration: float = 0.5,
        easing: str = 'linear'
    ):
        super().__init__(
            target=target,
            from_params={'opacity': from_opacity},
            to_params={'opacity': to_opacity},
            duration=duration,
            easing=easing
        )


class FadeOut(Animate):
    """
    Fade component out from opaque to transparent.

    Example:
        FadeOut(target='logo', duration=0.5)
        FadeOut(target='logo', from_opacity=1.0, to_opacity=0.0, duration=0.5)
    """

    def __init__(
        self,
        target: str,
        from_opacity: float = 1.0,
        to_opacity: float = 0.0,
        duration: float = 0.5,
        easing: str = 'linear'
    ):
        super().__init__(
            target=target,
            from_params={'opacity': from_opacity},
            to_params={'opacity': to_opacity},
            duration=duration,
            easing=easing
        )


class SlideIn(Animate):
    """
    Slide component in from a direction.

    Example:
        SlideIn(target='logo', direction='left', duration=1.0)
        SlideIn(target='logo', direction='top', distance=50, duration=1.0)
    """

    def __init__(
        self,
        target: str,
        direction: str = 'left',
        distance: Optional[int] = None,
        duration: float = 1.0,
        easing: str = 'ease_out'
    ):
        """
        Initialize slide-in animation.

        Args:
            target: Component ID to animate
            direction: Direction to slide from ('left', 'right', 'top', 'bottom')
            distance: Distance to slide (default: 64 pixels, roughly component width)
            duration: Animation duration in seconds
            easing: Easing function name
        """
        if distance is None:
            distance = 64  # Default distance

        # Map direction to relative parameters (using _int variants for pixel positions)
        if direction == 'left':
            from_rel_int = {'x': -distance}
            to_rel_int = {'x': 0}
        elif direction == 'right':
            from_rel_int = {'x': distance}
            to_rel_int = {'x': 0}
        elif direction == 'top':
            from_rel_int = {'y': -distance}
            to_rel_int = {'y': 0}
        elif direction == 'bottom':
            from_rel_int = {'y': distance}
            to_rel_int = {'y': 0}
        else:
            raise ValueError(f"Unknown direction: {direction}. Use 'left', 'right', 'top', or 'bottom'")

        super().__init__(
            target=target,
            from_params_rel_int=from_rel_int,
            to_params_rel_int=to_rel_int,
            duration=duration,
            easing=easing
        )


class SlideOut(Animate):
    """
    Slide component out in a direction.

    Example:
        SlideOut(target='logo', direction='right', duration=1.0)
        SlideOut(target='logo', direction='bottom', distance=50, duration=1.0)
    """

    def __init__(
        self,
        target: str,
        direction: str = 'right',
        distance: Optional[int] = None,
        duration: float = 1.0,
        easing: str = 'ease_in'
    ):
        """
        Initialize slide-out animation.

        Args:
            target: Component ID to animate
            direction: Direction to slide to ('left', 'right', 'top', 'bottom')
            distance: Distance to slide (default: 64 pixels)
            duration: Animation duration in seconds
            easing: Easing function name
        """
        if distance is None:
            distance = 64

        # Map direction to relative parameters (using _int variants for pixel positions)
        if direction == 'left':
            from_rel_int = {'x': 0}
            to_rel_int = {'x': -distance}
        elif direction == 'right':
            from_rel_int = {'x': 0}
            to_rel_int = {'x': distance}
        elif direction == 'top':
            from_rel_int = {'y': 0}
            to_rel_int = {'y': -distance}
        elif direction == 'bottom':
            from_rel_int = {'y': 0}
            to_rel_int = {'y': distance}
        else:
            raise ValueError(f"Unknown direction: {direction}. Use 'left', 'right', 'top', or 'bottom'")

        super().__init__(
            target=target,
            from_params_rel_int=from_rel_int,
            to_params_rel_int=to_rel_int,
            duration=duration,
            easing=easing
        )



class Sequence(Animation):
    """
    Run animations one after another in sequence.

    Example:
        Sequence(
            SlideIn(target="logo", direction="left"),
            FadeIn(target="text"),
            SlideOut(target="logo", direction="right")
        )
    """

    def __init__(self, *animations: Animation):
        """Initialize sequence of animations."""
        if not animations:
            raise ValueError("Sequence requires at least one animation")

        target = animations[0].target
        total_duration = sum(anim.duration for anim in animations)

        super().__init__(target=target, duration=total_duration, easing="linear")
        self.animations = list(animations)
        self.current_index = 0

    def update(self, state: dict, elapsed: float) -> bool:
        """Update current animation in sequence."""
        if self.completed:
            return True

        # Calculate elapsed time for current animation
        elapsed_in_sequence = elapsed
        for i in range(self.current_index):
            elapsed_in_sequence -= self.animations[i].duration

        current_anim = self.animations[self.current_index]
        is_complete = current_anim.update(state, elapsed_in_sequence)

        if is_complete:
            self.current_index += 1

            if self.current_index >= len(self.animations):
                self.completed = True
                return True

        return False

    def reset(self):
        """Reset sequence and all contained animations."""
        super().reset()
        self.current_index = 0
        for anim in self.animations:
            anim.reset()


class Parallel(Animation):
    """Run multiple animations simultaneously."""

    def __init__(self, *animations: Animation):
        if not animations:
            raise ValueError("Parallel requires at least one animation")

        target = animations[0].target
        max_duration = max(anim.duration for anim in animations)

        super().__init__(target=target, duration=max_duration, easing="linear")
        self.animations = list(animations)

    def update(self, state: dict, elapsed: float) -> bool:
        if self.completed:
            return True

        all_complete = True
        for anim in self.animations:
            if not anim.completed:
                if not anim.update(state, elapsed):
                    all_complete = False

        if all_complete:
            self.completed = True

        return all_complete

    def reset(self):
        super().reset()
        for anim in self.animations:
            anim.reset()


class GravityJump(Animation):
    """
    Physics-based gravity jump animation.

    Uses real projectile motion physics: y(t) = y0 + v0*t - 0.5*g*t^2

    Parameters:
    - target: Component ID to animate
    - param: Parameter to animate (default: 'y')
    - height: Peak height of jump in pixels (positive = jump up)
    - duration: Time for complete jump (up and down)

    The class automatically solves for initial velocity (v0) and gravity (g)
    to create a realistic parabolic arc that:
    - Starts at current position
    - Reaches 'height' pixels above start at the peak (t=duration/2)
    - Lands back at starting position at t=duration

    Physics solution:
    - Peak occurs at t = T/2
    - At peak, velocity = 0: v0 = g*T/2
    - At peak, position = y0 + height: y0 + height = y0 + v0*(T/2) - 0.5*g*(T/2)^2
    - Solving: v0 = 4*height/T, g = 8*height/T^2
    """

    def __init__(
        self,
        target: str,
        param: str = 'y',
        height: int = 10,
        duration: float = 1.0,
    ):
        super().__init__(target=target, duration=duration, easing='linear')

        self.param = param
        self.height = height  # Peak height in pixels

        # Cache resolved physics
        self._y0: Optional[float] = None  # Initial position
        self._v0: Optional[float] = None  # Initial velocity
        self._g: Optional[float] = None   # Gravity constant

    def reset(self):
        """Reset animation to initial state, clearing cached physics."""
        super().reset()
        self._y0 = None
        self._v0 = None
        self._g = None

    def _resolve_physics(self, state: dict):
        """Solve for initial velocity and gravity to reach specified height."""
        if self._y0 is not None:
            return  # Already resolved

        # Get current position
        self._y0 = state.get(self.param, 0)

        # Solve for physics constants to reach 'height' at peak (t=T/2)
        # v0 = 4*height/T
        # g = 8*height/T^2
        T = self.duration
        self._v0 = 4 * self.height / T
        self._g = 8 * self.height / (T * T)

    def _apply(self, state: dict, progress: float):
        """Apply physics-based position at given progress."""
        # Resolve physics on first apply
        if self._y0 is None:
            self._resolve_physics(state)

        # Calculate position using physics: y(t) = y0 + v0*t - 0.5*g*t^2
        # Note: for screen coordinates, up is negative, so we subtract the displacement
        t = progress * self.duration
        displacement = self._v0 * t - 0.5 * self._g * (t * t)
        y = self._y0 - displacement  # Subtract because screen y increases downward

        # Round to integer
        y = int(y)

        # Apply to state
        state[self.param] = y


class GravityFallIn(Animation):
    """
    Physics-based gravity fall-in animation with bouncing.

    Object falls from above the screen to target position with realistic bounces.
    Each bounce uses coefficient of restitution physics: v_bounce = v_impact * bounce_coef

    Parameters:
    - target: Component ID to animate
    - param: Parameter to animate (default: 'y')
    - fall_distance: How far to fall (pixels from above screen)
    - duration: Total time for fall and all bounces
    - bounce_coef: Coefficient of restitution (0.0-1.0), velocity retained after bounce
    - max_bounces: Maximum number of bounces (default: 3)
    - gravity: Gravity constant in pixels/second^2 (default: 800)

    Physics:
    - Free fall: v = sqrt(2 * g * h)
    - Bounce velocity: v_new = v_old * bounce_coef
    - Bounce height: h_new = (v_new^2) / (2 * g)
    """

    def __init__(
        self,
        target: str,
        param: str = 'y',
        fall_distance: int = 32,
        duration: float = 2.0,
        bounce_coef: float = 0.5,
        max_bounces: int = 3,
        gravity: float = 800.0,
    ):
        super().__init__(target=target, duration=duration, easing='linear')

        self.param = param
        self.fall_distance = fall_distance
        self.bounce_coef = bounce_coef
        self.max_bounces = max_bounces
        self.gravity = gravity

        # Cache resolved values
        self._target_y: Optional[float] = None  # Final resting position
        self._start_y: Optional[float] = None   # Starting position (above screen)
        self._bounces: Optional[List[Tuple[float, float, float]]] = None  # (t_start, t_end, height)

    def reset(self):
        """Reset animation to initial state."""
        super().reset()
        self._target_y = None
        self._start_y = None
        self._bounces = None

    def _resolve_physics(self, state: dict):
        """Calculate bounce timings and heights using physics."""
        if self._target_y is not None:
            return  # Already resolved

        # Get target position (where object should end up)
        self._target_y = state.get(self.param, 0)

        # Start position is above the screen
        self._start_y = self._target_y - self.fall_distance

        # Calculate bounce sequence
        self._bounces = []

        # Initial fall velocity when hitting ground: v = sqrt(2 * g * h)
        import math
        v_impact = math.sqrt(2 * self.gravity * self.fall_distance)

        # Time for initial fall: t = sqrt(2 * h / g)
        t_fall = math.sqrt(2 * self.fall_distance / self.gravity)

        current_time = t_fall
        current_velocity = v_impact

        # Calculate each bounce
        for bounce_num in range(self.max_bounces):
            # Velocity after bounce (coefficient of restitution)
            bounce_velocity = current_velocity * self.bounce_coef

            if bounce_velocity < 1.0:  # Stop if bounce is too small
                break

            # Height of this bounce: h = v^2 / (2 * g)
            bounce_height = (bounce_velocity * bounce_velocity) / (2 * self.gravity)

            # Time to reach peak and fall back: t = 2 * v / g
            bounce_duration = 2 * bounce_velocity / self.gravity

            # Store bounce info: (start_time, end_time, height)
            self._bounces.append((current_time, current_time + bounce_duration, bounce_height))

            current_time += bounce_duration
            current_velocity = bounce_velocity

        # Scale time to fit within duration
        if current_time > 0:
            self._time_scale = self.duration / current_time
        else:
            self._time_scale = 1.0

    def _apply(self, state: dict, progress: float):
        """Apply physics-based position at given progress."""
        if self._target_y is None:
            self._resolve_physics(state)

        # Current time in animation
        t = progress * self.duration

        # Convert to physics time
        t_physics = t / self._time_scale

        # Initial fall time
        import math
        t_fall = math.sqrt(2 * self.fall_distance / self.gravity)

        if t_physics <= t_fall:
            # Still in initial fall: y = y0 + 0.5 * g * t^2
            fall_dist = 0.5 * self.gravity * (t_physics * t_physics)
            y = self._start_y + fall_dist
        else:
            # Check which bounce we're in
            y = self._target_y  # Default to resting position

            for bounce_start, bounce_end, bounce_height in self._bounces:
                if bounce_start <= t_physics <= bounce_end:
                    # Time within this bounce
                    t_bounce = t_physics - bounce_start
                    bounce_duration = bounce_end - bounce_start

                    # Bounce is a parabola: peak at t_bounce = duration/2
                    # y(t) = y0 - v0*t + 0.5*g*t^2
                    v0 = math.sqrt(2 * self.gravity * bounce_height)
                    y = self._target_y - (v0 * t_bounce - 0.5 * self.gravity * (t_bounce * t_bounce))
                    break

        # Apply to state
        state[self.param] = int(y)


class Loop(Animation):
    """Loop an animation a specified number of times or infinitely."""

    def __init__(self, animation: Animation, count: Optional[int] = None):
        duration = float("inf") if count is None else animation.duration * count

        super().__init__(target=animation.target, duration=duration, easing="linear")
        self.animation = animation
        self.count = count
        self.current_iteration = 0

    def update(self, state: dict, elapsed: float) -> bool:
        if self.completed:
            return True

        # Calculate which iteration we're in and elapsed time within that iteration
        iteration = int(elapsed / self.animation.duration)
        elapsed_in_iteration = elapsed % self.animation.duration

        # Check if we've moved to a new iteration
        if iteration > self.current_iteration:
            self.animation.reset()
            self.current_iteration = iteration

        # Check if we've exceeded the count
        if self.count is not None and self.current_iteration >= self.count:
            self.completed = True
            return True

        # Update the animation
        self.animation.update(state, elapsed_in_iteration)

        return False

    def reset(self):
        super().reset()
        self.current_iteration = 0
        self.animation.reset()


# Helper functions for bulk animation creation

def slide_in_all(
    targets,
    start_time: float = 0.0,
    duration: float = 1.0,
    easing: str = 'ease_out'
) -> list:
    """
    Create slide-in animations for multiple components.

    Args:
        targets: Either:
                 - Dict mapping component_id to direction ('left', 'right', 'top', 'bottom')
                 - List of component IDs (auto-assigns reasonable directions)
        start_time: When all animations should start (relative to scene start)
        duration: Duration for all animations
        easing: Easing function for all animations

    Returns:
        List of (start_time, Animation) tuples

    Example:
        # Explicit directions
        slide_in_all({'title': 'left', 'logo': 'top', 'subtitle': 'right'})

        # Auto-assign directions (cycles through left, top, right, bottom)
        slide_in_all(['title', 'logo', 'subtitle'])
    """
    # Auto-assign directions if targets is a list
    if isinstance(targets, list):
        directions = ['left', 'top', 'right', 'bottom']
        targets = {target: directions[i % len(directions)] for i, target in enumerate(targets)}

    animations = []
    for target, direction in targets.items():
        anim = SlideIn(target=target, direction=direction, duration=duration, easing=easing)
        animations.append((start_time, anim))
    return animations


def slide_out_all(
    targets,
    start_time: float = 0.0,
    duration: float = 1.0,
    easing: str = 'ease_in'
) -> list:
    """
    Create slide-out animations for multiple components.

    Args:
        targets: Either:
                 - Dict mapping component_id to direction ('left', 'right', 'top', 'bottom')
                 - List of component IDs (auto-assigns reasonable directions)
        start_time: When all animations should start (relative to scene start)
        duration: Duration for all animations
        easing: Easing function for all animations

    Returns:
        List of (start_time, Animation) tuples

    Example:
        # Explicit directions
        slide_out_all({'title': 'left', 'logo': 'bottom', 'subtitle': 'right'})

        # Auto-assign directions (cycles through left, bottom, right, top)
        slide_out_all(['title', 'logo', 'subtitle'])
    """
    # Auto-assign directions if targets is a list
    if isinstance(targets, list):
        directions = ['left', 'bottom', 'right', 'top']
        targets = {target: directions[i % len(directions)] for i, target in enumerate(targets)}

    animations = []
    for target, direction in targets.items():
        anim = SlideOut(target=target, direction=direction, duration=duration, easing=easing)
        animations.append((start_time, anim))
    return animations


def fade_in_all(
    targets: list,
    start_time: float = 0.0,
    duration: float = 1.0,
    easing: str = 'ease_out'
) -> list:
    """
    Create fade-in animations for multiple components.

    Args:
        targets: List of component IDs
        start_time: When all animations should start (relative to scene start)
        duration: Duration for all animations
        easing: Easing function for all animations

    Returns:
        List of (start_time, Animation) tuples

    Example:
        fade_in_all(['title', 'logo', 'subtitle'], start_time=0.0, duration=1.0)
    """
    animations = []
    for target in targets:
        anim = FadeIn(target=target, duration=duration, easing=easing)
        animations.append((start_time, anim))
    return animations


def fade_out_all(
    targets: list,
    start_time: float = 0.0,
    duration: float = 1.0,
    easing: str = 'ease_in'
) -> list:
    """
    Create fade-out animations for multiple components.

    Args:
        targets: List of component IDs
        start_time: When all animations should start (relative to scene start)
        duration: Duration for all animations
        easing: Easing function for all animations

    Returns:
        List of (start_time, Animation) tuples

    Example:
        fade_out_all(['title', 'logo', 'subtitle'], start_time=0.0, duration=1.0)
    """
    animations = []
    for target in targets:
        anim = FadeOut(target=target, duration=duration, easing=easing)
        animations.append((start_time, anim))
    return animations
