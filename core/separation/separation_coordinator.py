"""
separation_coordinator.py - Routes separation requests to appropriate engines
"""

import numpy as np
from typing import Dict, List
import time

from .separation_data import SeparationMethod, SeparationResult, SeparationChannel
from .engines.spot_color_engine import SpotColorEngine
from .engines.simulated_process_engine import SimulatedProcessEngine
from .engines.index_color_engine import IndexColorEngine
from .engines.cmyk_engine import CMYKEngine
from .engines.rgb_engine import RGBEngine
from .engines.hybrid_ai_engine import HybridAIEngine


class SeparationCoordinator:
    """
    Coordinates separation execution
    Routes to appropriate engine based on selected method
    """

    def __init__(self, api_key: str = None):
        """
        Initialize coordinator with all engines

        Args:
            api_key: Optional Gemini API key (for future Hybrid AI support)
        """
        self.api_key = api_key

        # Initialize all engines
        self.engines = {
            SeparationMethod.SPOT_COLOR: SpotColorEngine(),
            SeparationMethod.SIMULATED_PROCESS: SimulatedProcessEngine(),
            SeparationMethod.INDEX_COLOR: IndexColorEngine(),
            SeparationMethod.CMYK: CMYKEngine(),
            SeparationMethod.RGB: RGBEngine(),
            SeparationMethod.HYBRID_AI: HybridAIEngine(api_key),  # Phase 4
        }

    def execute_separation(
        self,
        rgb_array: np.ndarray,
        method: SeparationMethod,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> SeparationResult:
        """
        Execute separation using specified method

        Args:
            rgb_array: Image as numpy array (H, W, 3)
            method: Selected separation method
            palette: Color palette from Color Match unit
            analysis_data: Analysis from Analyze unit
            parameters: Method-specific parameters

        Returns:
            SeparationResult with channels or error information
        """
        try:
            start_time = time.time()

            # Validate method
            if method not in self.engines:
                raise ValueError(f"Unsupported separation method: {method}")

            # Get appropriate engine
            engine = self.engines[method]

            print(f"  [Separation] Using {method.value} engine...")

            # Execute separation
            channels = engine.separate(
                rgb_array=rgb_array,
                palette=palette,
                analysis_data=analysis_data,
                parameters=parameters
            )

            # Calculate totals
            total_coverage = sum(ch.coverage_percentage for ch in channels)
            processing_time = time.time() - start_time

            print(f"  [Separation] OK: Created {len(channels)} channels in {processing_time:.2f}s")

            # Build result
            result = SeparationResult(
                channels=channels,
                method_used=method,
                success=True,
                processing_time=processing_time,
                palette_colors_used=len(palette),
                total_coverage=min(total_coverage, 100.0)  # Cap at 100%
            )

            return result

        except Exception as e:
            import traceback
            error_msg = f"Separation failed: {str(e)}"
            print(f"  [Separation] ERROR: {error_msg}")
            print(f"  [Separation] Traceback:\n{traceback.format_exc()}")

            return SeparationResult(
                channels=[],
                method_used=method,
                success=False,
                error_message=error_msg,
                processing_time=0.0
            )

    def get_available_methods(self) -> List[SeparationMethod]:
        """
        Get list of available separation methods

        Returns:
            List of SeparationMethod enums
        """
        return list(self.engines.keys())

    def get_default_parameters(self, method: SeparationMethod) -> Dict:
        """
        Get default parameters for a separation method

        Args:
            method: Separation method

        Returns:
            Dictionary of default parameters
        """
        defaults = {
            SeparationMethod.SPOT_COLOR: {
                'color_tolerance': 10.0,
            },
            SeparationMethod.SIMULATED_PROCESS: {
                'halftone_method': 'stochastic',
            },
            SeparationMethod.INDEX_COLOR: {
                'dither_method': 'floyd_steinberg',
            },
            SeparationMethod.CMYK: {},
            SeparationMethod.RGB: {},
        }

        return defaults.get(method, {})
