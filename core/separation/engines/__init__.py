"""
Separation Engines - Individual separation method implementations
"""

from .spot_color_engine import SpotColorEngine
from .simulated_process_engine import SimulatedProcessEngine
from .index_color_engine import IndexColorEngine
from .cmyk_engine import CMYKEngine
from .rgb_engine import RGBEngine

__all__ = [
    'SpotColorEngine',
    'SimulatedProcessEngine',
    'IndexColorEngine',
    'CMYKEngine',
    'RGBEngine',
]
