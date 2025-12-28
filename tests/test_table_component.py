#!/usr/bin/env python3
"""Test TableComponent."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matrix_scene_composer import (
    Orchestrator, Scene, TableComponent,
    Text4pxComponent, Text5pxComponent
)


def render_to_terminal(buffer):
    """Render buffer to terminal with ANSI true colors."""
    height, width = buffer.height, buffer.width
    for y in range(height):
        for x in range(width):
            r, g, b = buffer.get_pixel(x, y)
            print(f'\033[38;2;{r};{g};{b}m█\033[0m', end='')
        print()


def test_table_component():
    """Test TableComponent with different configurations."""

    print("\n=== Testing TableComponent with Text4pxComponent ===\n")

    width, height = 64, 32
    orch = Orchestrator(width=width, height=height, fps=10)
    scene = Scene(orch, width=width, height=height)

    # Sample data - system monitoring
    data = [
        {"name": "CPU", "temp": "45C", "load": "23%"},
        {"name": "GPU", "temp": "67C", "load": "89%"},
        {"name": "RAM", "temp": "42C", "load": "56%"},
    ]

    table = TableComponent(
        scene,
        data=data,
        text_component=Text4pxComponent,
        fgcolor=(255, 255, 255),
        header_fgcolor=(255, 255, 0),
        header_bgcolor=(0, 0, 128),
        cell_padding=1,
        show_borders=True,
        border_color=(64, 64, 64)
    )

    print(f"Table dimensions: {table.width}x{table.height}")
    print(f"Headers: {table.headers}")
    print(f"Column widths: {table.col_widths}")
    print()

    scene.add_component('table', table, position=(2, 2))

    orch.add_scene('test', scene)
    orch.transition_to('test')

    buffer = orch.render_single_frame(0.0)
    render_to_terminal(buffer)

    print("\n\n=== Testing TableComponent with Text5pxComponent ===\n")

    orch2 = Orchestrator(width=width, height=height, fps=10)
    scene2 = Scene(orch2, width=width, height=height)

    # Different data - scoreboard
    data2 = [
        {"rank": "1", "player": "ALICE", "score": "999"},
        {"rank": "2", "player": "BOB", "score": "877"},
        {"rank": "3", "player": "CARL", "score": "654"},
    ]

    table2 = TableComponent(
        scene2,
        data=data2,
        text_component=Text5pxComponent,
        fgcolor=(0, 255, 0),
        header_fgcolor=(0, 0, 0),
        header_bgcolor=(0, 255, 0),
        cell_padding=1,
        show_borders=True,
        border_color=(32, 32, 32)
    )

    print(f"Table dimensions: {table2.width}x{table2.height}")
    print(f"Headers: {table2.headers}")
    print(f"Column widths: {table2.col_widths}")
    print()

    scene2.add_component('table2', table2, position=(2, 2))

    orch2.add_scene('test2', scene2)
    orch2.transition_to('test2')

    buffer2 = orch2.render_single_frame(0.0)
    render_to_terminal(buffer2)

    print("\n\n=== Testing TableComponent without borders ===\n")

    orch3 = Orchestrator(width=width, height=height, fps=10)
    scene3 = Scene(orch3, width=width, height=height)

    # Minimal table
    data3 = [
        {"item": "A", "qty": "12"},
        {"item": "B", "qty": "34"},
    ]

    table3 = TableComponent(
        scene3,
        data=data3,
        text_component=Text4pxComponent,
        fgcolor=(255, 100, 0),
        header_bgcolor=(100, 50, 0),
        cell_padding=2,
        show_borders=False
    )

    print(f"Table dimensions: {table3.width}x{table3.height}")
    print(f"Headers: {table3.headers}")
    print(f"Column widths: {table3.col_widths}")
    print()

    scene3.add_component('table3', table3, position=(2, 2))

    orch3.add_scene('test3', scene3)
    orch3.transition_to('test3')

    buffer3 = orch3.render_single_frame(0.0)
    render_to_terminal(buffer3)

    print("\n\n=== Summary ===")
    print("TableComponent successfully renders structured data")
    print("- Supports Text4pxComponent and Text5pxComponent")
    print("- Auto-calculates column widths from content")
    print("- Optional borders and custom styling")
    print("- Perfect for LED matrix displays!")
    print()


if __name__ == "__main__":
    test_table_component()
