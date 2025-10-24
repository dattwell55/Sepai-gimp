"""
cmyk_engine.py - CMYK separation engine
Standard 4-color process separation
"""

import numpy as np
from typing import Dict, List
from ..separation_data import SeparationChannel


class CMYKEngine:
    """
    CMYK Separation Engine
    Standard 4-color process (Cyan, Magenta, Yellow, Black)
    """

    def separate(
        self,
        rgb_array: np.ndarray,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> List[SeparationChannel]:
        """
        Execute CMYK separation

        Args:
            rgb_array: Image as numpy array (H, W, 3)
            palette: Color palette (ignored for CMYK)
            analysis_data: Analysis results (ignored)
            parameters: Optional parameters

        Returns:
            List of 4 SeparationChannel objects (C, M, Y, K)
        """
        # Convert RGB to CMYK
        cmyk_array = self._rgb_to_cmyk(rgb_array)

        # Standard CMYK channel definitions
        cmyk_channels = [
            {
                'name': 'Cyan',
                'data': cmyk_array[:, :, 0],
                'rgb': (0, 255, 255),
                'angle': 15.0
            },
            {
                'name': 'Magenta',
                'data': cmyk_array[:, :, 1],
                'rgb': (255, 0, 255),
                'angle': 75.0
            },
            {
                'name': 'Yellow',
                'data': cmyk_array[:, :, 2],
                'rgb': (255, 255, 0),
                'angle': 0.0
            },
            {
                'name': 'Black',
                'data': cmyk_array[:, :, 3],
                'rgb': (0, 0, 0),
                'angle': 45.0
            }
        ]

        channels = []

        for idx, ch_info in enumerate(cmyk_channels):
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

    def _rgb_to_cmyk(self, rgb_array: np.ndarray) -> np.ndarray:
        """
        Convert RGB to CMYK

        Returns:
            CMYK array (H, W, 4) with values 0-255
        """
        # Normalize RGB to 0-1
        rgb_normalized = rgb_array.astype(np.float32) / 255.0

        # Calculate K (black) channel
        k = 1.0 - np.max(rgb_normalized, axis=2)

        # Calculate CMY channels
        # Avoid division by zero
        k_inv = 1.0 - k
        k_inv = np.where(k_inv == 0, 1e-10, k_inv)

        c = (1.0 - rgb_normalized[:, :, 0] - k) / k_inv
        m = (1.0 - rgb_normalized[:, :, 1] - k) / k_inv
        y = (1.0 - rgb_normalized[:, :, 2] - k) / k_inv

        # Stack and convert to 0-255 range
        cmyk = np.stack([c, m, y, k], axis=2)
        cmyk = np.clip(cmyk * 255, 0, 255).astype(np.uint8)

        return cmyk

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
