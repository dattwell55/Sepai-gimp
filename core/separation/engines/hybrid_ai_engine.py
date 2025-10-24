"""
hybrid_ai_engine.py - Main Hybrid AI Separation Engine

Coordinates the complete hybrid workflow:
1. AI Call #2: Analyze regions and recommend methods
2. Separate each region with appropriate method
3. Merge regional results into unified channels
"""

import numpy as np
from typing import List, Dict

from ..hybrid_data import HybridSeparationParameters
from ..separation_data import SeparationChannel
from ..region_analyzer import RegionAnalyzer
from ..regional_separator import RegionalSeparator
from ..channel_merger import ChannelMerger


class HybridAIEngine:
    """
    Main Hybrid AI Separation Engine
    Coordinates the complete hybrid workflow
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key

        # Initialize components
        self.region_analyzer = RegionAnalyzer(api_key)
        self.regional_separator = RegionalSeparator()
        self.channel_merger = ChannelMerger()

    def separate(
        self,
        rgb_array: np.ndarray,
        palette,
        analysis_data,
        parameters: Dict
    ) -> List[SeparationChannel]:
        """
        Execute complete hybrid AI separation

        This is the main entry point called by SeparationCoordinator
        when user selects Hybrid AI method

        Workflow:
        1. AI Call #2: Analyze regions and recommend methods
        2. Separate each region with appropriate method
        3. Merge regional results into unified channels

        Args:
            rgb_array: RGB image (H, W, 3)
            palette: User's color palette
            analysis_data: Analysis from Analyze unit
            parameters: Hybrid-specific parameters

        Returns:
            List of merged SeparationChannel objects
        """
        print("\n  [Hybrid AI] Starting hybrid separation...")

        # Convert RGB to LAB
        lab_image = self._rgb_to_lab(rgb_array)

        # Parse parameters
        hybrid_params = HybridSeparationParameters(
            min_region_size=parameters.get('min_region_size', 1000),
            edge_sensitivity=parameters.get('edge_sensitivity', 0.5),
            blend_edges=parameters.get('blend_edges', True),
            blend_radius=parameters.get('blend_radius', 15),
            prefer_spot_color=parameters.get('prefer_spot_color', True),
            allow_mixed_method=parameters.get('allow_mixed_method', True),
            detail_level=parameters.get('detail_level', 'high')
        )

        # ============================================================
        # STEP 1: AI REGION ANALYSIS (AI CALL #2)
        # ============================================================
        print("\n  [Hybrid AI] === AI CALL #2: Region Analysis ===")

        region_analysis = self.region_analyzer.analyze_regions(
            rgb_image=rgb_array,
            lab_image=lab_image,
            palette=palette,
            analysis_data=analysis_data,
            parameters=hybrid_params
        )

        print(f"\n  [Hybrid AI] Strategy: {region_analysis.strategy_summary}")
        print(f"  [Hybrid AI] Confidence: {int(region_analysis.overall_confidence * 100)}%")
        print(f"  [Hybrid AI] Regions: {region_analysis.region_count}")

        for region in region_analysis.regions:
            print(f"    - {region.id}: {region.region_type.value} -> {region.recommended_method.value}")

        # ============================================================
        # STEP 2: SEPARATE EACH REGION
        # ============================================================
        print("\n  [Hybrid AI] === Separating Regions ===")

        regional_results = self.regional_separator.separate_regions(
            rgb_image=rgb_array,
            lab_image=lab_image,
            region_analysis=region_analysis,
            palette=palette,
            analysis_data=analysis_data
        )

        # ============================================================
        # STEP 3: MERGE REGIONAL CHANNELS
        # ============================================================
        print("\n  [Hybrid AI] === Merging Channels ===")

        merged_channels = self.channel_merger.merge_regional_channels(
            regional_results=regional_results,
            palette=palette,
            image_shape=rgb_array.shape[:2],
            parameters=hybrid_params
        )

        print(f"\n  [Hybrid AI] OK Hybrid separation complete: {len(merged_channels)} channels")

        return merged_channels

    def _rgb_to_lab(self, rgb_array: np.ndarray) -> np.ndarray:
        """Convert RGB to LAB color space (simplified)"""
        # Normalize RGB to 0-1
        rgb_norm = rgb_array.astype(np.float32) / 255.0

        # Simple approximation of LAB
        # L = luminance
        L = 0.299 * rgb_norm[:, :, 0] + 0.587 * rgb_norm[:, :, 1] + 0.114 * rgb_norm[:, :, 2]
        L = L * 100  # Scale to 0-100

        # A and B channels (simplified)
        A = (rgb_norm[:, :, 0] - rgb_norm[:, :, 1]) * 128
        B = (rgb_norm[:, :, 1] - rgb_norm[:, :, 2]) * 128

        return np.stack([L, A, B], axis=2)
