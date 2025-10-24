"""
regional_separator.py - Applies separation methods to individual regions

Takes region analysis and applies the appropriate separation engine
to each region independently.
"""

import numpy as np
from typing import List, Dict

from .hybrid_data import RegionAnalysisResult, ImageRegion, RegionalSeparationResult
from .separation_data import SeparationMethod


class RegionalSeparator:
    """
    Applies appropriate separation method to each region
    """

    def __init__(self):
        # Initialize all separation engines
        from .engines.spot_color_engine import SpotColorEngine
        from .engines.simulated_process_engine import SimulatedProcessEngine
        from .engines.index_color_engine import IndexColorEngine

        self.spot_engine = SpotColorEngine()
        self.simulated_engine = SimulatedProcessEngine()
        self.index_engine = IndexColorEngine()

    def separate_regions(
        self,
        rgb_image: np.ndarray,
        lab_image: np.ndarray,
        region_analysis: RegionAnalysisResult,
        palette,
        analysis_data
    ) -> List[RegionalSeparationResult]:
        """
        Separate each region using its recommended method

        Args:
            rgb_image: Original RGB image
            lab_image: LAB color space image
            region_analysis: AI analysis results
            palette: Color palette
            analysis_data: Original analysis data

        Returns:
            List of regional separation results
        """
        regional_results = []

        for region in region_analysis.regions:
            print(f"    [Region {region.id}] Separating with {region.recommended_method.value}...")

            # Extract region image
            region_rgb = self._extract_region_image(rgb_image, region.mask)
            region_lab = self._extract_region_image(lab_image, region.mask)

            # Get appropriate engine
            engine = self._get_engine_for_method(region.recommended_method)

            # Get method-specific parameters
            parameters = self._get_parameters_for_region(region)

            # Execute separation
            try:
                channels = engine.separate(
                    rgb_array=region_rgb,
                    palette=palette,
                    analysis_data=analysis_data,
                    parameters=parameters
                )

                # Store result
                regional_results.append(RegionalSeparationResult(
                    region_id=region.id,
                    region=region,
                    method=region.recommended_method,
                    channels=channels,
                    success=True
                ))

                print(f"    [Region {region.id}] OK Created {len(channels)} channels")

            except Exception as e:
                print(f"    [Region {region.id}] ERROR Separation failed: {e}")

                # Store failure
                regional_results.append(RegionalSeparationResult(
                    region_id=region.id,
                    region=region,
                    method=region.recommended_method,
                    channels=[],
                    success=False,
                    error=str(e)
                ))

        return regional_results

    def _extract_region_image(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """
        Extract region from image, filling non-region with white
        """
        region_image = image.copy()

        # Set non-region pixels to white
        if len(image.shape) == 3:
            # RGB/LAB image
            if image.dtype == np.uint8:
                region_image[~mask] = [255, 255, 255]
            else:
                # LAB white is [100, 0, 0]
                region_image[~mask] = [100, 0, 0]
        else:
            # Grayscale
            region_image[~mask] = 255 if image.dtype == np.uint8 else 100

        return region_image

    def _get_engine_for_method(self, method: SeparationMethod):
        """Get appropriate separation engine"""
        if method == SeparationMethod.SPOT_COLOR:
            return self.spot_engine
        elif method == SeparationMethod.SIMULATED_PROCESS:
            return self.simulated_engine
        elif method == SeparationMethod.INDEX_COLOR:
            return self.index_engine
        else:
            # Fallback to index
            return self.index_engine

    def _get_parameters_for_region(self, region: ImageRegion) -> Dict:
        """Get method-specific parameters based on region characteristics"""

        if region.recommended_method == SeparationMethod.SPOT_COLOR:
            # Adjust tolerance based on edge sharpness
            tolerance = 15.0 if region.edge_sharpness > 0.8 else 20.0

            return {
                'color_tolerance': tolerance,
                'edge_smoothing': region.edge_sharpness < 0.7
            }

        elif region.recommended_method == SeparationMethod.SIMULATED_PROCESS:
            # Use error diffusion for gradients
            return {
                'dither_method': 'error_diffusion' if region.has_gradients else 'none',
                'halftone_method': 'stochastic'
            }

        elif region.recommended_method == SeparationMethod.INDEX_COLOR:
            # Use dithering if gradients present
            return {
                'dither_method': 'floyd_steinberg' if region.has_gradients else 'none'
            }

        return {}
