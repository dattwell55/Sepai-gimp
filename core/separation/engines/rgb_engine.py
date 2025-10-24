"""
rgb_engine.py - RGB separation engine
Simple 3-color RGB separation (fallback only)
"""

import numpy as np
from typing import Dict, List
from ..separation_data import SeparationChannel


class RGBEngine:
    """
    RGB Separation Engine
    Simple 3-channel RGB separation (rarely used in screen printing)
    Provided as a fallback/experimental option
    """

    def separate(
        self,
        rgb_array: np.ndarray,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> List[SeparationChannel]:
        """
        Execute RGB separation

        Args:
            rgb_array: Image as numpy array (H, W, 3)
            palette: Color palette (ignored for RGB)
            analysis_data: Analysis results (ignored)
            parameters: Optional parameters

        Returns:
            List of 3 SeparationChannel objects (R, G, B)
        """
        # Standard RGB channel definitions
        rgb_channels = [
            {
                'name': 'Red',
                'data': rgb_array[:, :, 0],
                'rgb': (255, 0, 0),
                'angle': 15.0
            },
            {
                'name': 'Green',
                'data': rgb_array[:, :, 1],
                'rgb': (0, 255, 0),
                'angle': 75.0
            },
            {
                'name': 'Blue',
                'data': rgb_array[:, :, 2],
                'rgb': (0, 0, 255),
                'angle': 45.0
            }
        ]

        channels = []

        for idx, ch_info in enumerate(rgb_channels):
            # Calculate statistics
            pixel_count = np.sum(ch_info['data'] > 0)
            coverage = (pixel_count / ch_info['data'].size) * 100

            # Create channel
            channel = SeparationChannel(
                name=ch_info['name'],
                data=ch_info['data'],
                color_info={
                    'rgb': ch_info['rgb'],
                    'lab': self._rgb_to_lab_single(ch_info['rgb']),
                    'pantone': None,
                    'hex': self._rgb_to_hex(ch_info['rgb'])
                },
                order=idx + 1,
                halftone_angle=ch_info['angle'],
                halftone_frequency=55.0,
                pixel_count=int(pixel_count),
                coverage_percentage=float(coverage)
            )

            channels.append(channel)

        return channels

    def _rgb_to_lab_single(self, rgb: tuple) -> tuple:
        """Convert single RGB color to LAB (simplified)"""
        # Normalize
        r, g, b = [x / 255.0 for x in rgb]

        # RGB to XYZ
        x = 0.4124 * r + 0.3576 * g + 0.1805 * b
        y = 0.2126 * r + 0.7152 * g + 0.0722 * b
        z = 0.0193 * r + 0.1192 * g + 0.9505 * b

        # XYZ to LAB
        x /= 0.95047
        y /= 1.0
        z /= 1.08883

        def f(t):
            return t ** (1/3) if t > 0.008856 else 7.787 * t + 16/116

        fx, fy, fz = f(x), f(y), f(z)

        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b_lab = 200 * (fy - fz)

        return (L, a, b_lab)

    def _rgb_to_hex(self, rgb: tuple) -> str:
        """Convert RGB tuple to hex string"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
