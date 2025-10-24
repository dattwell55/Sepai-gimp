"""
index_color_engine.py - Index color separation engine
Best for: 6-12 colors, balanced quality/cost
"""

import numpy as np
from typing import Dict, List, Tuple
from ..separation_data import SeparationChannel


class IndexColorEngine:
    """
    Index Color Separation Engine
    Quantizes image to palette colors with optional dithering
    """

    def separate(
        self,
        rgb_array: np.ndarray,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> List[SeparationChannel]:
        """
        Execute index color separation

        Args:
            rgb_array: Image as numpy array
            palette: Color palette
            analysis_data: Analysis results
            parameters: {'dither_method': str}

        Returns:
            List of SeparationChannel objects
        """
        dither_method = parameters.get('dither_method', 'floyd_steinberg')

        # Convert to LAB
        lab_array = self._rgb_to_lab(rgb_array)

        # Quantize to palette
        color_indices = self._quantize_to_palette(
            lab_array,
            [c['lab'] for c in palette],
            dither_method
        )

        # Create channel for each color
        channels = []

        for idx, color_info in enumerate(palette):
            # Extract pixels matching this color index
            mask = (color_indices == idx).astype(np.uint8) * 255

            # Calculate statistics
            pixel_count = np.sum(mask > 0)
            coverage = (pixel_count / mask.size) * 100

            # Create channel
            channel = SeparationChannel(
                name=color_info['name'],
                data=mask,
                color_info={
                    'rgb': color_info['rgb'],
                    'lab': color_info['lab'],
                    'pantone': color_info.get('pantone_code'),
                    'hex': self._rgb_to_hex(color_info['rgb'])
                },
                order=idx + 1,
                halftone_angle=45.0 + (idx * 15),
                halftone_frequency=55.0,
                pixel_count=int(pixel_count),
                coverage_percentage=float(coverage)
            )

            channels.append(channel)

        return channels

    def _rgb_to_lab(self, rgb_array: np.ndarray) -> np.ndarray:
        """Convert RGB to LAB"""
        rgb_normalized = rgb_array.astype(np.float32) / 255.0

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

        xyz_normalized = xyz / np.array([0.95047, 1.0, 1.08883])

        mask = xyz_normalized > 0.008856
        xyz_normalized[mask] = np.power(xyz_normalized[mask], 1/3)
        xyz_normalized[~mask] = 7.787 * xyz_normalized[~mask] + 16/116

        lab = np.zeros_like(xyz_normalized)
        lab[:, :, 0] = (116 * xyz_normalized[:, :, 1]) - 16
        lab[:, :, 1] = 500 * (xyz_normalized[:, :, 0] - xyz_normalized[:, :, 1])
        lab[:, :, 2] = 200 * (xyz_normalized[:, :, 1] - xyz_normalized[:, :, 2])

        return lab

    def _quantize_to_palette(
        self,
        lab_array: np.ndarray,
        palette_lab: List[Tuple[float, float, float]],
        dither_method: str
    ) -> np.ndarray:
        """
        Quantize image to palette colors

        Returns:
            Array of color indices
        """
        height, width = lab_array.shape[:2]
        color_indices = np.zeros((height, width), dtype=np.int32)

        palette_array = np.array(palette_lab)

        if dither_method == 'floyd_steinberg':
            # Floyd-Steinberg dithering
            lab_working = lab_array.copy().astype(np.float32)

            for y in range(height):
                for x in range(width):
                    old_pixel = lab_working[y, x]

                    # Find closest palette color
                    distances = np.sqrt(np.sum((palette_array - old_pixel) ** 2, axis=1))
                    closest_idx = np.argmin(distances)

                    new_pixel = palette_array[closest_idx]
                    color_indices[y, x] = closest_idx
                    lab_working[y, x] = new_pixel

                    # Calculate and distribute error
                    error = old_pixel - new_pixel

                    if x + 1 < width:
                        lab_working[y, x + 1] += error * 7/16
                    if y + 1 < height:
                        if x > 0:
                            lab_working[y + 1, x - 1] += error * 3/16
                        lab_working[y + 1, x] += error * 5/16
                        if x + 1 < width:
                            lab_working[y + 1, x + 1] += error * 1/16
        else:
            # No dithering - nearest neighbor (vectorized for speed)
            pixels = lab_array.reshape(-1, 3)
            distances = np.sqrt(np.sum((pixels[:, np.newaxis, :] - palette_array[np.newaxis, :, :]) ** 2, axis=2))
            color_indices = np.argmin(distances, axis=1).reshape(height, width)

        return color_indices

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
