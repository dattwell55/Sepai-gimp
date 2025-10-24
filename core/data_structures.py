#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Structures for SepAI Image Analysis
Defines core data models for image processing and analysis results
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np
from enum import Enum


class AnalysisLevel(Enum):
    """Analysis detail levels"""
    QUICK = "quick"
    STANDARD = "standard"
    DETAILED = "detailed"


@dataclass
class ImageDimensions:
    """Image dimension information"""
    original_width: int
    original_height: int
    original_dpi: float = 72.0
    working_width: int = 0
    working_height: int = 0

    def __post_init__(self):
        """Set working dimensions if not provided"""
        if self.working_width == 0:
            self.working_width = min(self.original_width, 800)
        if self.working_height == 0:
            # Maintain aspect ratio
            aspect_ratio = self.original_height / self.original_width
            self.working_height = int(self.working_width * aspect_ratio)


@dataclass
class ProcessedImageData:
    """Container for image data in different color spaces"""
    rgb_image: np.ndarray
    lab_image: Optional[np.ndarray] = None
    dimensions: Optional[ImageDimensions] = None
    source_filename: str = "untitled"
    source_filepath: str = ""

    def __post_init__(self):
        """Initialize dimensions if not provided"""
        if self.dimensions is None:
            height, width = self.rgb_image.shape[:2]
            self.dimensions = ImageDimensions(
                original_width=width,
                original_height=height
            )


@dataclass
class ColorCluster:
    """Represents a color cluster in the image"""
    center_rgb: Tuple[int, int, int]
    center_lab: Tuple[float, float, float]
    pixel_count: int
    percentage: float
    variance: float = 0.0
    is_dominant: bool = False


@dataclass
class ColorAnalysisResult:
    """Results from color analysis"""
    clusters: List[ColorCluster] = field(default_factory=list)
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    color_count_estimate: int = 4
    color_complexity: float = 0.5  # 0.0 = simple, 1.0 = complex
    has_gradients: bool = False
    has_fine_details: bool = False
    recommended_method: str = "spot_color"
    color_histogram: Optional[np.ndarray] = None
    unique_color_count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'clusters': [
                {
                    'center_rgb': c.center_rgb,
                    'center_lab': c.center_lab,
                    'pixel_count': int(c.pixel_count),
                    'percentage': float(c.percentage),
                    'variance': float(c.variance),
                    'is_dominant': c.is_dominant
                }
                for c in self.clusters
            ],
            'dominant_colors': [list(c) for c in self.dominant_colors],
            'color_count_estimate': self.color_count_estimate,
            'color_complexity': self.color_complexity,
            'has_gradients': self.has_gradients,
            'has_fine_details': self.has_fine_details,
            'recommended_method': self.recommended_method,
            'unique_color_count': self.unique_color_count
        }


@dataclass
class EdgeAnalysisResult:
    """Results from edge detection analysis"""
    edge_density: float = 0.0  # 0.0 = few edges, 1.0 = many edges
    edge_sharpness: float = 0.5  # 0.0 = soft, 1.0 = sharp
    has_fine_lines: bool = False
    has_halftones: bool = False
    detail_level: str = "medium"  # low, medium, high
    edge_map: Optional[np.ndarray] = None
    contour_count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'edge_density': float(self.edge_density),
            'edge_sharpness': float(self.edge_sharpness),
            'has_fine_lines': self.has_fine_lines,
            'has_halftones': self.has_halftones,
            'detail_level': self.detail_level,
            'contour_count': self.contour_count
        }


@dataclass
class TextureAnalysisResult:
    """Results from texture analysis"""
    texture_complexity: float = 0.5  # 0.0 = flat, 1.0 = highly textured
    dominant_patterns: List[str] = field(default_factory=list)
    noise_level: float = 0.0
    grain_size: str = "none"  # none, fine, medium, coarse
    has_screens: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'texture_complexity': float(self.texture_complexity),
            'dominant_patterns': self.dominant_patterns,
            'noise_level': float(self.noise_level),
            'grain_size': self.grain_size,
            'has_screens': self.has_screens
        }


@dataclass
class AnalysisDataModel:
    """Complete analysis results for an image"""
    image_dimensions: ImageDimensions
    color_analysis: ColorAnalysisResult
    edge_analysis: EdgeAnalysisResult
    texture_analysis: TextureAnalysisResult
    analysis_timestamp: float = 0.0
    cache_key: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'image_dimensions': {
                'original_width': self.image_dimensions.original_width,
                'original_height': self.image_dimensions.original_height,
                'original_dpi': self.image_dimensions.original_dpi,
                'working_width': self.image_dimensions.working_width,
                'working_height': self.image_dimensions.working_height
            },
            'color_analysis': self.color_analysis.to_dict(),
            'edge_analysis': self.edge_analysis.to_dict(),
            'texture_analysis': self.texture_analysis.to_dict(),
            'analysis_timestamp': self.analysis_timestamp,
            'cache_key': self.cache_key
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AnalysisDataModel':
        """Create from dictionary"""
        # Reconstruct ImageDimensions
        dims_data = data['image_dimensions']
        dimensions = ImageDimensions(
            original_width=dims_data['original_width'],
            original_height=dims_data['original_height'],
            original_dpi=dims_data.get('original_dpi', 72.0),
            working_width=dims_data['working_width'],
            working_height=dims_data['working_height']
        )

        # Reconstruct ColorAnalysisResult
        color_data = data['color_analysis']
        clusters = [
            ColorCluster(
                center_rgb=tuple(c['center_rgb']),
                center_lab=tuple(c['center_lab']),
                pixel_count=c['pixel_count'],
                percentage=c['percentage'],
                variance=c.get('variance', 0.0),
                is_dominant=c.get('is_dominant', False)
            )
            for c in color_data.get('clusters', [])
        ]

        color_analysis = ColorAnalysisResult(
            clusters=clusters,
            dominant_colors=[tuple(c) for c in color_data.get('dominant_colors', [])],
            color_count_estimate=color_data.get('color_count_estimate', 4),
            color_complexity=color_data.get('color_complexity', 0.5),
            has_gradients=color_data.get('has_gradients', False),
            has_fine_details=color_data.get('has_fine_details', False),
            recommended_method=color_data.get('recommended_method', 'spot_color'),
            unique_color_count=color_data.get('unique_color_count', 0)
        )

        # Reconstruct EdgeAnalysisResult
        edge_data = data['edge_analysis']
        edge_analysis = EdgeAnalysisResult(
            edge_density=edge_data.get('edge_density', 0.0),
            edge_sharpness=edge_data.get('edge_sharpness', 0.5),
            has_fine_lines=edge_data.get('has_fine_lines', False),
            has_halftones=edge_data.get('has_halftones', False),
            detail_level=edge_data.get('detail_level', 'medium'),
            contour_count=edge_data.get('contour_count', 0)
        )

        # Reconstruct TextureAnalysisResult
        texture_data = data['texture_analysis']
        texture_analysis = TextureAnalysisResult(
            texture_complexity=texture_data.get('texture_complexity', 0.5),
            dominant_patterns=texture_data.get('dominant_patterns', []),
            noise_level=texture_data.get('noise_level', 0.0),
            grain_size=texture_data.get('grain_size', 'none'),
            has_screens=texture_data.get('has_screens', False)
        )

        return cls(
            image_dimensions=dimensions,
            color_analysis=color_analysis,
            edge_analysis=edge_analysis,
            texture_analysis=texture_analysis,
            analysis_timestamp=data.get('analysis_timestamp', 0.0),
            cache_key=data.get('cache_key', '')
        )


@dataclass
class SeparationSettings:
    """Settings for color separation"""
    method: str = "spot_color"  # spot_color, cmyk, simulated_process, index
    num_colors: int = 4
    use_ai_suggestions: bool = True
    preserve_gradients: bool = True
    halftone_lpi: int = 55
    underbase: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'method': self.method,
            'num_colors': self.num_colors,
            'use_ai_suggestions': self.use_ai_suggestions,
            'preserve_gradients': self.preserve_gradients,
            'halftone_lpi': self.halftone_lpi,
            'underbase': self.underbase
        }
