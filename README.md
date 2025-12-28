# rpi-rgb-led-matrix-scene-composer

A high-level scene-based rendering engine for RGB LED matrices on Raspberry Pi.

## Overview

This library provides a clean, composable architecture for creating animated content on RGB LED matrices. It uses a scene-graph approach with components, scenes, and an orchestrator managing the render loop.

## Architecture

**Clean one-way dependency flow:**

```
Component (knows nothing)
    ↓
Scene (knows about Components)
    ↓
Orchestrator (knows about Scenes) [OPTIONAL]
```

**Core classes:**
- **Component**: Base class for renderable elements (text, tables, filters, etc.)
  - Pure, standalone - no knowledge of Scene
  - Renders to RenderBuffer when given time parameter
- **Scene**: Container for components with positioning and layering
  - Composes components
  - Can work standalone or with Orchestrator
- **DisplayTarget**: Abstraction for output (terminal emulator or physical matrix)
- **RenderBuffer**: Fixed-size RGB pixel buffer backed by numpy

**Optional (for multi-scene apps):**
- **Orchestrator**: Manages multiple scenes, transitions, and global time
  - Only needed when you have multiple scenes
  - Provides unified time source across scenes

## Features

- Simple Scene + Component composition model
- Automatic caching for static/slow-updating content
- Built-in components: Text, Tables, Rainbow filters
- Hardware-agnostic rendering
- Terminal emulator for development (no hardware needed!)
- Optional Orchestrator for multi-scene applications

## Installation

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/fredrikolis/rpi-rgb-led-matrix-scene-composer.git
cd rpi-rgb-led-matrix-scene-composer

# Run demos - they auto-install dependencies!
./run_terminal_demo.sh    # Terminal emulator (no hardware needed)
./run_matrix_demo.sh      # Physical RGB matrix (requires hardware)
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install core package
pip install -e .

# Install with PioMatter support (Raspberry Pi 5)
pip install -e ".[piomatter]"

# Install with RGB Matrix support (older Pi models)
pip install -e ".[rgbmatrix]"

# Install development tools
pip install -e ".[dev]"
```

## Quick Start - Scene + Components (Simplest)

Components are **pure** - they don't know about Scene. Scene composes components.

```python
from matrix_scene_composer import (
    Scene, TableComponent, Text4pxComponent, TerminalDisplayTarget
)
import time

# Step 1: Create components (standalone, no scene reference!)
data = [
    {"name": "CPU", "temp": "45C", "load": "23%"},
    {"name": "GPU", "temp": "67C", "load": "89%"},
]

table = TableComponent(
    data=data,
    text_component=Text4pxComponent,
    fgcolor=(255, 255, 255),
    header_bgcolor=(32, 32, 32),
    show_borders=True
)

# Step 2: Create scene and add components
scene = Scene(width=64, height=32)
scene.add_component('table', table, position=(2, 2))

# Step 3: Display
display = TerminalDisplayTarget(width=64, height=32)

with display:
    start_time = time.time()
    while time.time() - start_time < 5.0:
        current_time = time.time() - start_time
        buffer = scene.render(current_time)
        display.display(buffer)
        time.sleep(1/30)  # 30 FPS
```

## Advanced Example - Multi-Scene with Orchestrator

Use the Orchestrator **only when you need multiple scenes** with transitions.

```python
from matrix_scene_composer import (
    Orchestrator, Scene, TableComponent, RainbowFilter,
    Text5pxComponent, TerminalDisplayTarget
)
import time

# ============================================================================
# Data Sources (assume these fetch real data)
# ============================================================================

def get_system_stats():
    """Return current system metrics."""
    return [
        {"component": "CPU", "usage": "45%", "temp": "67C"},
        {"component": "RAM", "usage": "72%", "temp": "45C"},
        {"component": "GPU", "usage": "89%", "temp": "82C"},
    ]

def get_weather_info():
    """Return current weather."""
    return {
        "city": "Stockholm",
        "temp": "15°C",
        "condition": "Cloudy"
    }

# ============================================================================
# Scene Builders
# ============================================================================

def create_system_scene(width, height):
    """System monitoring scene with rainbow effect."""
    # Create components first (no scene reference!)
    data = get_system_stats()

    table = TableComponent(
        data=data,
        text_component=Text4pxComponent,
        fgcolor=(255, 255, 255),
        header_bgcolor=(32, 32, 32),
        cell_padding=1,
        show_borders=True
    )

    # Wrap with animated rainbow effect
    rainbow_table = RainbowFilter(
        source_component=table,
        color_key=(255, 255, 255),
        direction='horizontal',
        speed=0.5
    )

    # Create scene and add components
    scene = Scene(width, height)
    scene.add_component('table', rainbow_table, position=(2, 8))
    return scene

def create_weather_scene(width, height):
    """Weather display scene."""
    # Create components first (no scene reference!)
    weather = get_weather_info()
    text = f"{weather['city']}\n{weather['temp']}\n{weather['condition']}"

    weather_text = Text5pxComponent(
        text=text,
        fgcolor=(255, 255, 255),
        bgcolor=(0, 0, 64),
        padding=2
    )

    # Optional rainbow effect
    rainbow_weather = RainbowFilter(
        source_component=weather_text,
        color_key=(255, 255, 255),
        direction='vertical',
        speed=0.8
    )

    # Create scene and add components
    scene = Scene(width, height)
    scene.add_component('weather', rainbow_weather, position=(10, 5))
    return scene

# ============================================================================
# Main Application - Scene Rotation
# ============================================================================

def main():
    width, height = 64, 32

    # Set up display (swap for RGBMatrixDisplayTarget on real hardware)
    display = TerminalDisplayTarget(width, height)

    # Create orchestrator
    orch = Orchestrator(width, height, fps=30)
    orch.set_display_callback(display.display)

    # Build and register scenes (Orchestrator adopts them)
    orch.add_scene('system', create_system_scene(width, height))
    orch.add_scene('weather', create_weather_scene(width, height))

    # Define scene rotation schedule
    scenes = [
        ('system', 5.0),   # Show system for 5 seconds
        ('weather', 5.0),  # Show weather for 5 seconds
    ]

    # Start display and run with scene rotation
    with display:
        scene_idx = 0
        scene_start = time.time()
        start_time = time.time()

        orch.transition_to(scenes[scene_idx][0])

        try:
            while True:
                current_time = time.time() - start_time
                elapsed_in_scene = time.time() - scene_start
                scene_name, duration = scenes[scene_idx]

                # Check if time to switch scenes
                if elapsed_in_scene >= duration:
                    scene_idx = (scene_idx + 1) % len(scenes)
                    next_scene, _ = scenes[scene_idx]

                    # Rebuild scene with fresh data
                    if next_scene == 'system':
                        orch.scenes['system'] = create_system_scene(width, height)
                    elif next_scene == 'weather':
                        orch.scenes['weather'] = create_weather_scene(width, height)

                    orch.transition_to(next_scene)
                    scene_start = time.time()

                # Render current frame
                orch.time = current_time
                buffer = orch._render_frame()
                display.display(buffer)

                # Maintain FPS
                time.sleep(1.0 / orch.fps)

        except KeyboardInterrupt:
            print("\nShutting down...")

if __name__ == "__main__":
    main()
```

## Key Concepts

### Components are Pure and Composable

Components don't know about Scene - they're standalone, reusable building blocks.

```python
# Components are pure (no scene parameter!)
table = TableComponent(data=data, ...)

# Wrap with filter (composition)
rainbow_table = RainbowFilter(source_component=table, ...)

# Scene composes components
scene = Scene(width=64, height=32)
scene.add_component('background', bg_text, position=(0, 0), z_index=1)
scene.add_component('foreground', fg_text, position=(10, 10), z_index=2)
```

### Display Targets are Swappable

```python
# Development - terminal emulator
display = TerminalDisplayTarget(64, 32)

# Production - physical matrix
display = RGBMatrixDisplayTarget(64, 32, brightness=80)

# Same code works with both!
```

### Caching is Automatic

```python
class MyComponent(Component):
    def compute_state(self, time):
        # Return same state = cached rendering
        return ("static",)

        # Return different state = re-render
        return ("animated", int(time))
```

## Examples

See the `examples/` directory for more:
- `simple_scene_example.py` - **Start here!** Simplest Scene + Components example (terminal)
- `simple_scene_piomatter.py` - Same example but for physical hardware (PioMatter)
- `demo_rainbow_table.py` - Rainbow system monitor
- `demo_terminal_emulator.py` - Terminal display demo
- `demo_orchestrator.py` - Multi-scene showcase with Orchestrator

## Hardware Support

### Raspberry Pi 5 + Adafruit RGB Matrix Bonnet

Uses the `PioMatterDisplayTarget` with the modern PioMatter library:

```python
from matrix_scene_composer import PioMatterDisplayTarget

display = PioMatterDisplayTarget(
    width=64,
    height=32,
    n_addr_lines=4,      # 4 for 64x32 panel
    brightness=1.0       # 0.0 to 1.0
)
```

### Older Raspberry Pi Models

Uses the `RGBMatrixDisplayTarget` with the classic rpi-rgb-led-matrix library:

```python
from matrix_scene_composer import RGBMatrixDisplayTarget

display = RGBMatrixDisplayTarget(
    width=64,
    height=32,
    brightness=80
)
```

## Design Principles

- **Clean Architecture**: One-way dependencies (Component → Scene → Orchestrator)
- **Pure Components**: Components are standalone, no knowledge of Scene
- **KISS**: Keep it simple - start with Scene + Components, add Orchestrator only if needed
- **Fixed canvas**: Everything renders to defined width × height
- **Time as parameter**: Time is passed to `render(time)`, not stored in components
- **Composable**: Components wrap components (filters, effects, etc.)
- **Hardware agnostic**: Same code works on terminal or real matrix
