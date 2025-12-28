"""rpi-rgb-led-matrix-scene-composer - Scene-based rendering engine for RGB LED matrices."""

from .orchestrator import Orchestrator
from .scene import Scene
from .component import Component, cache_with_dict
from .render_buffer import RenderBuffer
from .text_component import TextComponent
from .table_component import TableComponent
from .image_component import ImageComponent
from .rainbow_filter import RainbowFilter
from .display_target import DisplayTarget
from .terminal_display_target import TerminalDisplayTarget
from .rgb_matrix_display_target import RGBMatrixDisplayTarget
from .piomatter_display_target import PioMatterDisplayTarget
from .animation import (
    Animation, Animate, FadeIn, FadeOut, SlideIn, SlideOut,
    Sequence, Parallel, Loop, GravityJump, GravityFallIn,
    slide_in_all, slide_out_all, fade_in_all, fade_out_all
)

__all__ = [
    'Orchestrator',
    'Scene',
    'Component',
    'RenderBuffer',
    'cache_with_dict',
    'TextComponent',
    'TableComponent',
    'ImageComponent',
    'RainbowFilter',
    'DisplayTarget',
    'TerminalDisplayTarget',
    'RGBMatrixDisplayTarget',
    'PioMatterDisplayTarget',
    'Animation',
    'Animate',
    'FadeIn',
    'FadeOut',
    'SlideIn',
    'SlideOut',
    'Sequence',
    'Parallel',
    'Loop',
    'GravityJump',
    'GravityFallIn',
    'slide_in_all',
    'slide_out_all',
    'fade_in_all',
    'fade_out_all',
]
