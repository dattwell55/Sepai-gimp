"""
hybrid_data.py - Data structures for Hybrid AI Separation

This module defines the data structures used by the Hybrid AI separation engine,
including region types, analysis results, and parameters.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
import numpy as np
from datetime import datetime

from .separation_data import SeparationMethod


class RegionType(str, Enum):
    """Types of image regions for hybrid separation"""
    VECTOR = "vector"           # Sharp edges, flat colors
    PHOTO = "photo"             # Soft edges, gradients, detail
    TEXT = "text"               # High-contrast text/linework
    MIXED = "mixed"             # Combination of characteristics
    BACKGROUND = "background"   # Uniform background area


class ContentComplexity(str, Enum):
    """Complexity level of region content"""
    SIMPLE = "simple"           # <3 colors, no gradients
    MODERATE = "moderate"       # 3-6 colors, some gradients
    COMPLEX = "complex"         # 6+ colors, many gradients


@dataclass
class ImageRegion:
    """Single segmented region of the image"""
    id: str
    region_type: RegionType
    complexity: ContentComplexity

    # Spatial information
    mask: np.ndarray            # Boolean mask (same size as image)
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    pixel_count: int
    coverage_percentage: float

    # Visual characteristics
    dominant_colors: List[Tuple[int, int, int]]  # Top 3-5 colors in region
    has_gradients: bool
    edge_sharpness: float       # 0-1, higher = sharper
    texture_score: float        # 0-1, higher = more texture

    # Separation strategy
    recommended_method: SeparationMethod
    method_confidence: float    # 0-1
    reasoning: str

    # Metadata
    priority: int               # 1-10, higher = more important


@dataclass
class RegionAnalysisResult:
    """Complete AI analysis of image regions"""

    # Segmentation results
    regions: List[ImageRegion]
    region_count: int

    # Overall strategy
    strategy_summary: str
    complexity_rating: str      # "simple", "moderate", "complex"

    # Method assignments
    method_assignments: Dict[str, SeparationMethod]  # region_id -> method

    # Quality predictions
    expected_quality: str       # "excellent", "good", "fair"
    expected_channels: int
    estimated_processing_time: float  # seconds

    # Confidence metrics
    overall_confidence: float   # 0-1
    confidence_by_region: Dict[str, float]

    # AI metadata
    gemini_response: Dict
    timestamp: str


@dataclass
class HybridSeparationParameters:
    """User-adjustable parameters for hybrid separation"""

    # Segmentation
    min_region_size: int = 1000         # Minimum pixels for separate region
    edge_sensitivity: float = 0.5       # 0-1, higher = more sensitive

    # Region blending
    blend_edges: bool = True
    blend_radius: int = 15              # Pixels for edge blending

    # Method preferences
    prefer_spot_color: bool = True      # Favor spot color when ambiguous
    allow_mixed_method: bool = True     # Allow "mixed" regions

    # Quality/speed tradeoff
    detail_level: str = "high"          # "low", "medium", "high"

    # Advanced
    custom_region_methods: Optional[Dict[str, SeparationMethod]] = None  # Override AI


@dataclass
class RegionalSeparationResult:
    """Result of separating a single region"""
    region_id: str
    region: ImageRegion
    method: SeparationMethod
    channels: List
    success: bool
    error: Optional[str] = None


class HybridValidationError(Exception):
    """Raised when hybrid separation validation fails"""
    pass
