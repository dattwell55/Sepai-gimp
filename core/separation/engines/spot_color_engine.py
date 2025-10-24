"""
spot_color_engine.py - Spot color separation engine
Best for: 2-6 flat colors, sharp edges, logos/graphics
"""

import numpy as np
from typing import Dict, List, Tuple
from ..separation_data import SeparationChannel


class SpotColorEngine:
    """
    Spot Color Separation Engine
    Creates one channel per palette color using LAB color matching
    """

    def separate(
        self,
        rgb_array: np.ndarray,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> List[SeparationChannel]:
        """
        Execute spot color separation

        Args:
            rgb_array: Image as numpy array (H, W, 3)
            palette: List of color dictionaries with 'rgb', 'lab', 'name'
            analysis_data: Analysis results (unused for spot color)
            parameters: {'color_tolerance': float}

        Returns:
            List of SeparationChannel objects
        """
        tolerance = parameters.get('color_tolerance', 10.0)

        # Convert RGB to LAB
        lab_array = self._rgb_to_lab(rgb_array)

        channels = []

        for idx, color_info in enumerate(palette):
            # Extract channel for this specific color
            channel_data = self._extract_color_channel(
                lab_array,
                color_info['lab'],
                tolerance
            )

            # Calculate statistics
            pixel_count = np.sum(channel_data > 0)
            coverage = (pixel_count / channel_data.size) * 100

            # Create channel
            channel = SeparationChannel(
                name=color_info['name'],
                data=channel_data,
                color_info={
                    'rgb': color_info['rgb'],
                    'lab': color_info['lab'],
                    'pantone': color_info.get('pantone_code'),
                    'hex': self._rgb_to_hex(color_info['rgb'])
                },
                order=idx + 1,
                halftone_angle=45.0 + (idx * 15),  # Avoid moiré
                halftone_frequency=55.0,
                pixel_count=int(pixel_count),
                coverage_percentage=float(coverage)
            )

            channels.append(channel)

        return channels

    def _rgb_to_lab(self, rgb_array: np.ndarray) -> np.ndarray:
        """Convert RGB to LAB color space"""
        # Normalize RGB to 0-1
        rgb_normalized = rgb_array.astype(np.float32) / 255.0

        # RGB to XYZ (simplified D65 illuminant)
        xyz = np.zeros_like(rgb_normalized)
        xyz[:, :, 0] = (0.4124 * rgb_normalized[:, :, 0] +
                       0.3576 * rgb_normalized[:, :, 1] +
                       0.1805 * rgb_normalized[:, :, 2])
        xyz[:, :, 1] = (0.2126 * rgb_normalized[:, :, 0] +
                       0.7152 * rgb_normalized[:, :, 1] +
                       0.0722 * rgb_normalized[:, :, 2])
        xyz[:, :, 2] = (0.0193 * rgb_normalized[:, :, 0] +
                       0.1192 * rgb_normalized[:, :, 1] +
                       0.9505 * rgb_normalized[:, :, 2])

        # XYZ to LAB
        xyz_normalized = xyz / np.array([0.95047, 1.0, 1.08883])

        mask = xyz_normalized > 0.008856
        xyz_normalized[mask] = np.power(xyz_normalized[mask], 1/3)
        xyz_normalized[~mask] = 7.787 * xyz_normalized[~mask] + 16/116

        lab = np.zeros_like(xyz_normalized)
        lab[:, :, 0] = (116 * xyz_normalized[:, :, 1]) - 16  # L
        lab[:, :, 1] = 500 * (xyz_normalized[:, :, 0] - xyz_normalized[:, :, 1])  # a
        lab[:, :, 2] = 200 * (xyz_normalized[:, :, 1] - xyz_normalized[:, :, 2])  # b

        return lab

    def _extract_color_channel(
        self,
        lab_array: np.ndarray,
        target_lab: Tuple[float, float, float],
        tolerance: float
    ) -> np.ndarray:
        """
        Extract channel for specific color using LAB distance

        Args:
            lab_array: Image in LAB space
            target_lab: Target color in LAB [L, a, b]
            tolerance: Delta-E tolerance

        Returns:
            Grayscale channel (0-255)
        """
        height, width = lab_array.shape[:2]
        channel_data = np.zeros((height, width), dtype=np.uint8)

        target_lab_array = np.array(target_lab)

        # Calculate Delta-E (Euclidean distance in LAB)
        delta_e = np.sqrt(np.sum((lab_array - target_lab_array) ** 2, axis=2))

        # Map to grayscale: closer match = brighter
        mask = delta_e <= tolerance
        # Inverse mapping: 0 distance = 255, tolerance distance = 0
        channel_data[mask] = (255 * (1 - delta_e[mask] / tolerance)).astype(np.uint8)

        return channel_data

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
