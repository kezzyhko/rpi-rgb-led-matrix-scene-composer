"""Scrolling text demo with focus and manual scrolling."""

import queue
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from matrix_scene_composer import (Component, RGBMatrixDisplayTarget, Scene,
                                   TerminalDisplayTarget, TextComponent,
                                   VStack)


def input_thread(input_queue):
    """Background thread for input handling."""
    try:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(fd)

            while True:
                ch = sys.stdin.read(1)

                # Handle arrow keys (escape sequences)
                if ch == "\x1b":
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A":
                            input_queue.put("UP")
                        elif ch3 == "B":
                            input_queue.put("DOWN")
                        elif ch3 == "C":
                            input_queue.put("RIGHT")
                        elif ch3 == "D":
                            input_queue.put("LEFT")
                elif ch == "q":
                    input_queue.put("QUIT")
                    break
                elif ch:
                    input_queue.put(ch)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except:
        pass


def main():
    WIDTH = 64
    HEIGHT = 32
    USE_HARDWARE = False

    if USE_HARDWARE:
        display = RGBMatrixDisplayTarget(width=WIDTH, height=HEIGHT, brightness=80)
    else:
        display = TerminalDisplayTarget(
            width=WIDTH, height=HEIGHT, use_half_blocks=True, square_pixels=True
        )

    scene = Scene(width=WIDTH, height=HEIGHT)

    # Create layout - automatic vertical stacking
    layout = VStack(width=WIDTH, height=HEIGHT, spacing=2, alignment="center", padding=2)

    # Add components to layout
    layout.add(
        "title",
        TextComponent(
            "SCROLLING TEXT DEMO",
            font_height=5,
            max_width=WIDTH - 4,
            fgcolor=(255, 100, 0),
            autoscroll="X",
            scroll_speed=15.0,
            scroll_pause=1.5,
        ),
    )

    layout.add(
        "msg1",
        TextComponent(
            "THIS MESSAGE IS TOO LONG TO FIT",
            font_height=4,
            max_width=WIDTH - 4,
            fgcolor=(0, 255, 100),
            autoscroll="X",
            scroll_speed=20.0,
            scroll_pause=1.0,
        ),
    )

    layout.add(
        "msg2",
        TextComponent(
            "USE ARROWS TO FOCUS AND SCROLL",
            font_height=4,
            max_width=WIDTH - 4,
            fgcolor=(100, 150, 255),
            autoscroll="X",
            scroll_speed=25.0,
            scroll_pause=1.0,
        ),
    )

    layout.add(
        "msg3",
        TextComponent(
            "FAST SCROLL HERE... WOW!",
            font_height=4,
            max_width=WIDTH - 4,
            fgcolor=(255, 255, 0),
            autoscroll="X",
            scroll_speed=40.0,
            scroll_pause=0.5,
        ),
    )

    # Add layout to scene
    scene.add_child("layout", layout, position=(0, 0))

    # Enable debug rendering by default
    Component.DEBUG_RENDER = True

    # Input handling setup
    input_queue = queue.Queue()
    has_input = False

    try:
        import termios

        thread = threading.Thread(target=input_thread, args=(input_queue,), daemon=True)
        thread.start()
        has_input = True
        print("Controls: UP/DOWN arrows to focus, LEFT/RIGHT arrows to scroll, 'q' to quit")
    except:
        pass

    with display:
        start_time = time.time()
        fps = 30
        frame_duration = 1.0 / fps

        try:
            while True:
                frame_start = time.time()
                current_time = time.time() - start_time

                # Handle input (non-blocking)
                if has_input:
                    try:
                        while True:
                            key = input_queue.get_nowait()

                            if key == "QUIT":
                                return
                            elif key == "DEBUG":
                                Component.DEBUG_RENDER = not Component.DEBUG_RENDER
                            elif key == "UP":
                                # Get layout and focus previous
                                layout_comp = scene.children.get("layout")
                                if layout_comp and hasattr(layout_comp.component, "focus_previous"):
                                    layout_comp.component.focus_previous()
                            elif key == "DOWN":
                                # Get layout and focus next
                                layout_comp = scene.children.get("layout")
                                if layout_comp and hasattr(layout_comp.component, "focus_next"):
                                    layout_comp.component.focus_next()
                            elif key in ("LEFT", "RIGHT"):
                                # Get focused component from layout
                                layout_comp = scene.children.get("layout")
                                if layout_comp and hasattr(
                                    layout_comp.component, "get_focused_component"
                                ):
                                    focused = layout_comp.component.get_focused_component()
                                    if focused and hasattr(focused, "scroll_by"):
                                        dx = -3 if key == "LEFT" else 3
                                        focused.scroll_by(dx)
                    except queue.Empty:
                        pass

                # Re-enable autoscroll for unfocused components
                layout_comp = scene.children.get("layout")
                if layout_comp:
                    for child_id, child_instance in layout_comp.component.children:
                        component = child_instance
                        if hasattr(component, "_autoscroll_enabled") and hasattr(
                            component, "_needs_scroll"
                        ):
                            if component.focused:
                                component._autoscroll_enabled = False
                            else:
                                component._autoscroll_enabled = True

                buffer = scene.render(current_time)
                display.display(buffer)

                elapsed = time.time() - frame_start
                sleep_time = max(0, frame_duration - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nShutting down...")


if __name__ == "__main__":
    main()
