"""Demo app for ProgressBar and Scrollbar components with scene switching."""

import queue
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from matrix_scene_composer import (Component, FadeIn, FadeOut, HStack,
                                   ProgressBar, RGBMatrixDisplayTarget, Scene,
                                   Scrollbar, SlideIn, SlideOut,
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
                elif ch == "d":
                    input_queue.put("DEBUG")
                elif ch == "j":
                    input_queue.put("SCENE_NEXT")
                elif ch == "k":
                    input_queue.put("SCENE_PREV")
                elif ch:
                    input_queue.put(ch)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except:
        pass


def create_progress_scene(width, height):
    """Create scene demonstrating progress bars."""
    scene = Scene(
        width=width,
        height=height,
        entrance_animations=[
            (0.0, SlideIn(target="layout", direction="left", duration=0.5, easing="ease_out")),
            (0.3, FadeIn(target="layout", duration=0.3)),
        ],
        exit_animations=[
            (0.0, SlideOut(target="layout", direction="right", duration=0.5, easing="ease_in")),
            (0.0, FadeOut(target="layout", duration=0.3)),
        ],
    )

    layout = VStack(width=width, height=height, spacing=3, alignment="center", padding=2)

    # Title
    layout.add("title", TextComponent("PROGRESS BAR DEMO", font_height=5, fgcolor=(255, 200, 0)))

    # Horizontal progress bar with label
    layout.add(
        "progress1",
        ProgressBar(
            width=width - 8,
            height=7,
            progress=0.0,
            orientation="horizontal",
            fill_color=(0, 255, 0),
            empty_color=(32, 32, 32),
            border_color=(64, 64, 64),
            show_label=True,
            label_font_height=4,
        ),
    )

    # Horizontal progress bar without label
    layout.add(
        "progress2",
        ProgressBar(
            width=width - 8,
            height=5,
            progress=0.0,
            orientation="horizontal",
            fill_color=(255, 100, 0),
            empty_color=(32, 32, 32),
            border_color=(64, 64, 64),
            show_label=False,
        ),
    )

    # Horizontal progress bar with custom label
    layout.add(
        "progress3",
        ProgressBar(
            width=width - 8,
            height=7,
            progress=0.0,
            orientation="horizontal",
            fill_color=(0, 100, 255),
            empty_color=(32, 32, 32),
            border_color=(64, 64, 64),
            show_label=True,
            label_text="LOADING",
            label_font_height=4,
        ),
    )

    scene.add_child("layout", layout, position=(0, 0))

    return scene


def create_scrollbar_scene(width, height):
    """Create scene demonstrating scrollbars."""
    scene = Scene(
        width=width,
        height=height,
        entrance_animations=[
            (0.0, SlideIn(target="layout", direction="right", duration=0.5, easing="ease_out")),
            (0.3, FadeIn(target="layout", duration=0.3)),
        ],
        exit_animations=[
            (0.0, SlideOut(target="layout", direction="left", duration=0.5, easing="ease_in")),
            (0.0, FadeOut(target="layout", duration=0.3)),
        ],
    )

    layout = HStack(width=width, height=height, spacing=2, alignment="center", padding=2)

    # Left side - vertical scrollbars
    left_stack = VStack(
        width=width // 2 - 2, height=height - 4, spacing=2, alignment="center", padding=1
    )

    left_stack.add("title1", TextComponent("VERTICAL", font_height=4, fgcolor=(255, 200, 0)))

    left_stack.add(
        "vscroll1",
        Scrollbar(
            width=2,
            height=height - 16,
            orientation="vertical",
            viewport_size=100,
            content_size=300,
            scroll_position=0,
            track_color=(32, 32, 32),
            thumb_color=(128, 128, 255),
            arrow_color=(64, 64, 64),
        ),
    )

    # Right side - horizontal scrollbar
    right_stack = VStack(
        width=width // 2 - 2, height=height - 4, spacing=2, alignment="center", padding=1
    )

    right_stack.add("title2", TextComponent("HORIZONTAL", font_height=4, fgcolor=(255, 200, 0)))

    right_stack.add(
        "hscroll1",
        Scrollbar(
            width=width // 2 - 8,
            height=2,
            orientation="horizontal",
            viewport_size=64,
            content_size=200,
            scroll_position=0,
            track_color=(32, 32, 32),
            thumb_color=(255, 128, 128),
            arrow_color=(64, 64, 64),
        ),
    )

    right_stack.add(
        "info",
        TextComponent(
            "USE ARROWS",
            font_height=4,
            fgcolor=(100, 255, 100),
            max_width=width // 2 - 8,
            autoscroll="X",
        ),
    )

    layout.add("left", left_stack)
    layout.add("right", right_stack)

    scene.add_child("layout", layout, position=(0, 0))

    return scene


def main():
    WIDTH = 64
    HEIGHT = 32
    USE_HARDWARE = True

    if USE_HARDWARE:
        display = RGBMatrixDisplayTarget(width=WIDTH, height=HEIGHT, brightness=80)
    else:
        display = TerminalDisplayTarget(
            width=WIDTH, height=HEIGHT, use_half_blocks=False, square_pixels=False
        )

    # Create scenes
    scenes = [
        ("progress", create_progress_scene(WIDTH, HEIGHT)),
        ("scrollbar", create_scrollbar_scene(WIDTH, HEIGHT)),
    ]
    current_scene_idx = 0
    current_scene = scenes[current_scene_idx][1]
    switching_scene = False
    switch_target_idx = 0

    # Enable debug rendering
    Component.DEBUG_RENDER = True

    # Input handling setup
    input_queue = queue.Queue()
    has_input = False

    try:
        import termios

        thread = threading.Thread(target=input_thread, args=(input_queue,), daemon=True)
        thread.start()
        has_input = True
        print("Controls: J/K=switch scene, ARROWS=scroll, D=debug, Q=quit")
    except:
        pass

    current_scene.on_enter()

    with display:
        start_time = time.time()
        fps = 30
        frame_duration = 1.0 / fps

        try:
            while True:
                frame_start = time.time()
                current_time = time.time() - start_time

                scene_name = scenes[current_scene_idx][0]

                # Handle input (non-blocking)
                if has_input:
                    try:
                        while True:
                            key = input_queue.get_nowait()

                            if key == "QUIT":
                                return
                            elif key == "DEBUG":
                                Component.DEBUG_RENDER = not Component.DEBUG_RENDER
                            elif key == "SCENE_NEXT" and not switching_scene:
                                switching_scene = True
                                switch_target_idx = (current_scene_idx + 1) % len(scenes)
                                current_scene.on_exit(
                                    current_scene._time if hasattr(current_scene, "_time") else 0.0
                                )
                            elif key == "SCENE_PREV" and not switching_scene:
                                switching_scene = True
                                switch_target_idx = (current_scene_idx - 1) % len(scenes)
                                current_scene.on_exit(
                                    current_scene._time if hasattr(current_scene, "_time") else 0.0
                                )
                            elif key in ("UP", "DOWN", "LEFT", "RIGHT"):
                                # Handle scrollbar controls
                                if scene_name == "scrollbar":
                                    layout_comp = current_scene.children.get("layout")
                                    if layout_comp:
                                        # Get vertical scrollbar
                                        for child_id, child in layout_comp.component.children:
                                            if child_id == "left":
                                                for sub_id, sub_child in child.children:
                                                    if sub_id == "vscroll1" and isinstance(
                                                        sub_child, Scrollbar
                                                    ):
                                                        if key == "UP":
                                                            sub_child.set_scroll_position(
                                                                sub_child.scroll_position - 10
                                                            )
                                                        elif key == "DOWN":
                                                            sub_child.set_scroll_position(
                                                                sub_child.scroll_position + 10
                                                            )
                                            elif child_id == "right":
                                                for sub_id, sub_child in child.children:
                                                    if sub_id == "hscroll1" and isinstance(
                                                        sub_child, Scrollbar
                                                    ):
                                                        if key == "LEFT":
                                                            sub_child.set_scroll_position(
                                                                sub_child.scroll_position - 10
                                                            )
                                                        elif key == "RIGHT":
                                                            sub_child.set_scroll_position(
                                                                sub_child.scroll_position + 10
                                                            )
                    except queue.Empty:
                        pass

                # Update scene time
                current_scene._time = current_time

                # Check if scene transition is complete
                if switching_scene:
                    scene_time = current_scene._time
                    if current_scene._check_phase_complete(scene_time):
                        # Switch to new scene
                        current_scene_idx = switch_target_idx
                        current_scene = scenes[current_scene_idx][1]
                        current_scene.reset()  # Add this line
                        current_scene.on_enter()
                        switching_scene = False
                        start_time = time.time()
                        current_time = 0.0
                        scene_name = scenes[current_scene_idx][0]

                # Update progress bars based on time
                if scene_name == "progress":
                    layout_comp = current_scene.children.get("layout")
                    if layout_comp:
                        # Animate progress bars
                        progress = (current_time % 3.0) / 3.0  # 3 second cycle

                        for child_id, child in layout_comp.component.children:
                            if isinstance(child, ProgressBar):
                                if child_id == "progress1":
                                    child.set_progress(progress)
                                elif child_id == "progress2":
                                    # Different speed
                                    child.set_progress((current_time % 2.0) / 2.0)
                                elif child_id == "progress3":
                                    # Reverse direction
                                    child.set_progress(1.0 - progress)

                buffer = current_scene.render(current_time)
                display.display(buffer)

                elapsed = time.time() - frame_start
                sleep_time = max(0, frame_duration - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nShutting down...")


if __name__ == "__main__":
    main()
