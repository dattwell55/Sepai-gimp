"""
simulated_process_engine.py - Simulated process separation engine
Best for: Photos, gradients, complex artwork
"""

import numpy as np
from typing import Dict, List, Tuple
from ..separation_data import SeparationChannel


class SimulatedProcessEngine:
    """
    Simulated Process Separation Engine
    Uses spectral decomposition for photorealistic results
    """

    def separate(
        self,
        rgb_array: np.ndarray,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> List[SeparationChannel]:
        """
        Execute simulated process separation

        Args:
            rgb_array: Image as numpy array (H, W, 3)
            palette: Color palette
            analysis_data: Analysis results
            parameters: {'halftone_method': str}

        Returns:
            List of SeparationChannel objects
        """
        halftone_method = parameters.get('halftone_method', 'stochastic')

        # Convert to LAB
        lab_array = self._rgb_to_lab(rgb_array)

        channels = []

        for idx, color_info in enumerate(palette):
            # Calculate ink contribution using spectral separation
            channel_data = self._spectral_separation(
                lab_array,
                color_info['lab'],
                [c['lab'] for c in palette]
            )

            # Apply halftoning/dithering
            if halftone_method == 'error_diffusion':
                channel_data = self._apply_error_diffusion(channel_data)

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
                halftone_angle=45.0 + (idx * 15),
                halftone_frequency=65.0,  # Higher for photos
                pixel_count=int(pixel_count),
                coverage_percentage=float(coverage)
            )

            channels.append(channel)

        return channels

    def _rgb_to_lab(self, rgb_array: np.ndarray) -> np.ndarray:
        """Convert RGB to LAB (reuse from SpotColorEngine)"""
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

    def _spectral_separation(
        self,
        lab_array: np.ndarray,
        target_ink_lab: Tuple[float, float, float],
        all_inks_lab: List[Tuple[float, float, float]]
    ) -> np.ndarray:
        """
        Calculate ink contribution using spectral decomposition
        Uses inverse distance weighting
        """
        height, width = lab_array.shape[:2]
        channel_data = np.zeros((height, width), dtype=np.float32)

        target_lab = np.array(target_ink_lab)
        palette_lab = np.array(all_inks_lab)

        # Find target ink index
        target_idx = None
        for i, ink_lab in enumerate(all_inks_lab):
            if np.allclose(ink_lab, target_ink_lab, atol=0.1):
                target_idx = i
                break

        if target_idx is None:
            return channel_data.astype(np.uint8)

        # Vectorized calculation for efficiency
        # Reshape lab_array to (H*W, 3) for batch processing
        pixels = lab_array.reshape(-1, 3)

        # Calculate distances to all inks for all pixels at once
        # Broadcasting: pixels (H*W, 3) - palette_lab (N, 3) -> (H*W, N, 3)
        distances = np.sqrt(np.sum((pixels[:, np.newaxis, :] - palette_lab[np.newaxis, :, :]) ** 2, axis=2))

        # Inverse distance weighting
        weights = 1.0 / (distances + 1e-6)
        weights_normalized = weights / np.sum(weights, axis=1, keepdims=True)

        # Contribution of target ink
        contribution = weights_normalized[:, target_idx]

        # Reshape back to image dimensions and scale to 0-255
        channel_data = (contribution * 255).reshape(height, width)

        return np.clip(channel_data, 0, 255).astype(np.uint8)

    def _apply_error_diffusion(self, channel_data: np.ndarray) -> np.ndarray:
        """Apply Floyd-Steinberg error diffusion dithering"""
        height, width = channel_data.shape
        dithered = channel_data.copy().astype(np.float32)

        for y in range(height):
            for x in range(width):
                old_val = dithered[y, x]
                new_val = 255 if old_val > 127 else 0
                dithered[y, x] = new_val

                error = old_val - new_val

                # Distribute error
                if x + 1 < width:
                    dithered[y, x + 1] += error * 7/16
                if y + 1 < height:
                    if x > 0:
                        dithered[y + 1, x - 1] += error * 3/16
                    dithered[y + 1, x] += error * 5/16
                    if x + 1 < width:
                        dithered[y + 1, x + 1] += error * 1/16

        return np.clip(dithered, 0, 255).astype(np.uint8)

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
