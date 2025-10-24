"""
separation_data.py - Data structures for separation module
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict


class SeparationMethod(str, Enum):
    """Available separation methods"""
    SPOT_COLOR = "spot_color"           # Best for: 2-6 flat colors
    SIMULATED_PROCESS = "simulated_process"  # Best for: Photos, gradients
    INDEX_COLOR = "index_color"         # Best for: 6-12 colors, balanced
    CMYK = "cmyk"                       # Optional: Standard 4-color
    RGB = "rgb"                         # Optional: Fallback only
    HYBRID_AI = "hybrid_ai"             # Advanced: Region-based AI (Phase 4)


@dataclass
class MethodRecommendation:
    """AI recommendation for a separation method"""
    method: SeparationMethod
    method_name: str
    score: float              # 0-100
    confidence: float         # 0-1
    reasoning: str

    strengths: List[str]
    limitations: List[str]
    best_for: str

    expected_results: Dict    # channel_count, quality, complexity, cost
    palette_utilization: Dict # colors_used, percentage


@dataclass
class SeparationChannel:
    """Single separated color channel"""
    name: str
    data: 'numpy.ndarray'     # Grayscale channel data (H, W)
    color_info: Dict          # RGB, LAB, Pantone, etc.
    order: int                # Layer order (1 = first/bottom)

    # Halftone settings (optional, for reference)
    halftone_angle: float = 45.0
    halftone_frequency: float = 55.0

    # Statistics
    pixel_count: int = 0
    coverage_percentage: float = 0.0


@dataclass
class SeparationResult:
    """Complete separation result"""
    channels: List[SeparationChannel]
    method_used: SeparationMethod
    success: bool
    error_message: str = ""
    processing_time: float = 0.0

    # Metadata
    palette_colors_used: int = 0
    total_coverage: float = 0.0
