"""
Separation Module - AI-powered color separation for screen printing
Phase 1: Core separation engines
Phase 2: AI method recommendation
Phase 3: GTK user interface
Phase 4: Hybrid AI separation
"""

from .separation_data import SeparationMethod, MethodRecommendation
from .separation_coordinator import SeparationCoordinator
from .method_analyzer import AIMethodAnalyzer
from .hybrid_data import (
    RegionType, ContentComplexity, ImageRegion,
    RegionAnalysisResult, HybridSeparationParameters
)
from .region_analyzer import RegionAnalyzer
from .engines.hybrid_ai_engine import HybridAIEngine

__all__ = [
    'SeparationMethod',
    'MethodRecommendation',
    'SeparationCoordinator',
    'AIMethodAnalyzer',
    # Phase 4 - Hybrid AI
    'RegionType',
    'ContentComplexity',
    'ImageRegion',
    'RegionAnalysisResult',
    'HybridSeparationParameters',
    'RegionAnalyzer',
    'HybridAIEngine',
]
