# rpi-rgb-led-matrix-scene-composer

A high-level scene-based rendering engine for RGB LED matrices on Raspberry Pi.

## Overview

This library provides a clean, composable architecture for creating animated content on RGB LED matrices. It uses a scene-graph approach with components, layouts, and scenes managing positioning and animations.

## Architecture

**Clean one-way dependency flow:**

```
Component (pure, standalone)
    ↓
Layout (automatic positioning)
    ↓
Scene (composition + animations)
```

**Core classes:**
- **Component**: Base class for renderable elements (text, tables, progress bars, images, etc.)
- **Layout**: Automatic positioning (VStack, HStack, Grid, Absolute)
- **Scene**: Container for components with animations and focus management
- **DisplayTarget**: Abstraction for output (terminal emulator or physical matrix)

## Installation

```bash
# Clone the repository
git clone https://github.com/fredrikolis/rpi-rgb-led-matrix-scene-composer.git
cd rpi-rgb-led-matrix-scene-composer

# Install core package
pip install -e .

# Install with hardware support
pip install -e ".[piomatter]"    # Raspberry Pi 5
pip install -e ".[rgbmatrix]"    # Older Pi models
```

## Quick Start

```python
from matrix_scene_composer import (
    Scene, TextComponent, VStack, TerminalDisplayTarget
)
import time

# Create display (swap for RGBMatrixDisplayTarget on hardware)
display = TerminalDisplayTarget(width=64, height=32)

# Create scene with automatic layout
scene = Scene(width=64, height=32)
layout = VStack(width=64, height=32, spacing=2, alignment='center')

# Add components - no manual positioning needed
layout.add("title", TextComponent("HELLO WORLD", font_height=5))
layout.add("message", TextComponent("EASY LAYOUTS", font_height=4))

scene.add_child("layout", layout, position=(0, 0))

# Render loop
with display:
    start = time.time()
    while time.time() - start < 5:
        buffer = scene.render(time.time() - start)
        display.display(buffer)
        time.sleep(1/30)
```

## Components

### TextComponent
Bitmap text with automatic scrolling.

```python
text = TextComponent(
    text="SCROLLING MESSAGE",
    font_height=5,              # 4-16px available
    max_width=64,               # Enable scrolling
    autoscroll='X',             # Auto-scroll or 'NONE'
    scroll_speed=20.0,
    fgcolor=(255, 100, 0)
)

# Manual scrolling
text.scroll_by(dx=5)
text.set_text("NEW TEXT")       # Update without resetting scroll
```

### TableComponent
Data tables with scrolling support.

```python
table = TableComponent(
    data=[
        {"name": "CPU", "temp": "45C", "load": "23%"},
        {"name": "GPU", "temp": "67C", "load": "89%"}
    ],
    font_height=4,
    show_borders=True,
    max_width=60,               # Enable horizontal scroll
    max_height=24,              # Enable vertical scroll
    autoscroll='Y'              # 'X', 'Y', 'BOTH', or 'NONE'
)

# Manual scrolling
table.scroll_by(dy=5)
```

### ProgressBar
Progress indicators with optional labels.

```python
progress = ProgressBar(
    width=50,
    height=7,
    progress=0.75,              # 0.0 to 1.0
    orientation='horizontal',   # or 'vertical'
    show_label=True,
    label_text="LOADING"        # or None for percentage
)

progress.set_progress(0.9)
```

### Scrollbar
Scrollbar indicators for showing scroll position.

```python
scrollbar = Scrollbar(
    width=6,
    height=32,
    orientation='vertical',
    viewport_size=100,
    content_size=300,
    scroll_position=50
)

scrollbar.set_scroll_position(100)
```

### ImageComponent
Display PNG, JPG, GIF images with alpha support.

```python
image = ImageComponent("logo.png")
```

### RainbowFilter
Apply animated rainbow gradients to any component.

```python
rainbow = RainbowFilter(
    source_component=text,
    direction='horizontal',     # 'vertical', 'diagonal'
    speed=1.0
)
```

## Layouts

Automatically position components without manual coordinates.

### VStack - Vertical Stack
```python
layout = VStack(
    width=64,
    height=32,
    spacing=2,
    alignment='center',         # 'left', 'center', 'right'
    padding=2
)
layout.add("item1", component1)
layout.add("item2", component2)
```

### HStack - Horizontal Stack
```python
layout = HStack(
    width=64,
    height=32,
    spacing=2,
    alignment='center',         # 'top', 'center', 'bottom'
    padding=2
)
```

### Grid - Grid Layout
```python
layout = Grid(
    width=64,
    height=32,
    columns=3,
    spacing=2,
    padding=2
)
```

### Absolute - Manual Positioning
```python
layout = Absolute(width=64, height=32)
layout.add("logo", logo, position=(10, 10))
layout.center("title")
layout.align_top_right("status", padding=2)
```

### ZStack - Layered Stack
```python
layout = ZStack(
    width=64,
    height=32,
    alignment='center'          # All children at same position
)
```

Layouts can be nested inside other layouts.

## Animations

```python
from matrix_scene_composer import SlideIn, FadeIn, FadeOut

scene = Scene(
    width=64,
    height=32,
    entrance_animations=[
        (0.0, SlideIn(target="logo", direction='left', duration=0.5, easing='ease_out'))
    ],
    exit_animations=[
        (0.0, FadeOut(target="logo", duration=0.3))
    ]
)
```

**Available animations:**
- `SlideIn`, `SlideOut` - Slide from/to direction
- `FadeIn`, `FadeOut` - Opacity transitions
- `Animate` - Animate any component property
- `GravityJump`, `GravityFallIn` - Physics-based animations
- `Sequence` - Run animations in sequence
- `Parallel` - Run animations simultaneously
- `Loop` - Loop an animation

**Easing functions:** `linear`, `ease_in`, `ease_out`, `ease_in_out`, `bounce`, `elastic`, `gravity`

## Focus & Input Handling

Components can be focused for keyboard/input control.

```python
# Scene manages focus
scene.focus_next()              # Focus next focusable component
scene.focus_previous()          # Focus previous
scene.set_focus("component_id") # Focus specific component

focused = scene.get_focused_component()
if focused and hasattr(focused, 'scroll_by'):
    focused.scroll_by(dx=5)     # Scroll focused component

# Focusable components: TextComponent (when scrollable), TableComponent (when scrollable)
```

## Lifecycle Hooks

Components support lifecycle callbacks.

```python
component.on_mount(lambda: print("Mounted!"))
component.on_unmount(lambda: print("Unmounted!"))
component.on_focus_gain(lambda: print("Focused!"))
component.on_focus_lost(lambda: print("Lost focus!"))
```

## Debug Rendering

Enable debug mode to visualize focused components with purple outlines.

```python
from matrix_scene_composer import Component

Component.DEBUG_RENDER = True   # Enable debug rendering
```

## Display Targets

### TerminalDisplayTarget
Development without hardware.

```python
display = TerminalDisplayTarget(
    width=64,
    height=32,
    use_half_blocks=True,       # Better vertical resolution
    square_pixels=True,         # Square-ish pixels
    show_logs=True              # Show log output below matrix
)
```

### RGBMatrixDisplayTarget
Physical matrix for older Raspberry Pi models.

```python
display = RGBMatrixDisplayTarget(
    width=64,
    height=32,
    brightness=80
)
```

### PioMatterDisplayTarget
Raspberry Pi 5 with Adafruit Matrix Bonnet.

```python
display = PioMatterDisplayTarget(
    width=64,
    height=32,
    n_addr_lines=4,             # 4 for 64x32, 5 for 64x64
    brightness=1.0
)
```

## Examples

- `examples/scroll_demo.py` - Text scrolling with focus and manual control
- `examples/progress_scrollbar_demo.py` - Progress bars and scrollbars with scene switching
- See `examples/` directory for more

## Design Principles

- **Pure Components**: Standalone, reusable building blocks
- **Automatic Layout**: No manual coordinate calculations
- **Focus Management**: Built-in keyboard/input support
- **Hardware Agnostic**: Same code works on terminal or physical matrix
- **Composable**: Components wrap components (filters, effects)
- **Cached Rendering**: Automatic performance optimization

## Links

- [MIT License](LICENSE)
- [Original repo](https://github.com/fredrikolis/rpi-rgb-led-matrix-scene-composer) (gone now)
- [Another reupload from PyPI](https://github.com/krruzic/rpi-rgb-led-matrix-scene-composer)
