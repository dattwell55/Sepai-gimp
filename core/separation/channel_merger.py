"""
channel_merger.py - Intelligently merges channels from different regions

Takes the results from regional separations and merges them into
unified palette channels with smooth blending at boundaries.
"""

import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

from .hybrid_data import HybridSeparationParameters, RegionalSeparationResult
from .separation_data import SeparationChannel

# Try to import CV2 for blending
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python not installed. Using fallback blending.")


class ChannelMerger:
    """
    Intelligently merges channels from different regions
    """

    def merge_regional_channels(
        self,
        regional_results: List[RegionalSeparationResult],
        palette,
        image_shape: Tuple[int, int],
        parameters: HybridSeparationParameters
    ) -> List[SeparationChannel]:
        """
        Merge channels from all regions into unified palette channels

        Args:
            regional_results: List of regional separation results
            palette: Color palette
            image_shape: (height, width) of final image
            parameters: Hybrid parameters (for blending)

        Returns:
            List of merged SeparationChannel objects
        """
        height, width = image_shape
        merged_channels = []

        print("    [Merge] Combining regional channels...")

        # Get palette colors
        colors = self._extract_palette_colors(palette)

        # Create one channel per palette color
        for color_idx, color in enumerate(colors):
            print(f"    [Merge] Processing {color['name']}...")

            # Initialize merged channel data
            merged_data = np.zeros((height, width), dtype=np.float32)

            # Accumulate contributions from each region
            for regional in regional_results:
                if not regional.success:
                    continue

                region = regional.region
                channels = regional.channels
                mask = region.mask

                # Find matching color channel in this region
                matching_channel = self._find_matching_channel(channels, color)

                if matching_channel is not None:
                    # Add contribution with mask
                    if parameters.blend_edges:
                        # Smooth blend at region edges
                        blended_mask = self._create_blended_mask(
                            mask,
                            blend_radius=parameters.blend_radius
                        )
                        merged_data += matching_channel.data.astype(np.float32) * blended_mask
                    else:
                        # Hard edge
                        merged_data[mask] = np.maximum(
                            merged_data[mask],
                            matching_channel.data[mask].astype(np.float32)
                        )

            # Normalize and convert to uint8
            merged_data = np.clip(merged_data, 0, 255).astype(np.uint8)

            # Calculate statistics
            pixel_count = np.sum(merged_data > 0)
            coverage = (pixel_count / merged_data.size) * 100

            # Create merged channel
            channel = SeparationChannel(
                name=color['name'],
                data=merged_data,
                color_info=color,
                order=color_idx + 1,
                halftone_angle=45.0 + (color_idx * 15),
                halftone_frequency=55.0,
                pixel_count=int(pixel_count),
                coverage_percentage=float(coverage)
            )

            merged_channels.append(channel)
            print(f"    [Merge] OK {color['name']}: {coverage:.1f}% coverage")

        return merged_channels

    def _extract_palette_colors(self, palette) -> List[Dict]:
        """Extract color information from palette"""
        colors = []

        if hasattr(palette, 'colors'):
            for c in palette.colors:
                colors.append({
                    'name': c.name,
                    'rgb': c.rgb,
                    'lab': c.lab if hasattr(c, 'lab') else (0, 0, 0),
                    'pantone': c.pantone_code if hasattr(c, 'pantone_code') else None,
                    'hex': self._rgb_to_hex(c.rgb)
                })
        elif isinstance(palette, list):
            # Palette is already a list of colors
            for i, c in enumerate(palette):
                if isinstance(c, dict):
                    colors.append(c)
                else:
                    colors.append({
                        'name': f'Color {i+1}',
                        'rgb': c.rgb if hasattr(c, 'rgb') else (0, 0, 0),
                        'lab': c.lab if hasattr(c, 'lab') else (0, 0, 0),
                        'hex': self._rgb_to_hex(c.rgb if hasattr(c, 'rgb') else (0, 0, 0))
                    })

        return colors

    def _find_matching_channel(
        self,
        channels: List[SeparationChannel],
        target_color: Dict
    ) -> SeparationChannel:
        """Find channel matching target color"""
        for ch in channels:
            # Match by name or RGB
            ch_rgb = ch.color_info.get('rgb') if isinstance(ch.color_info, dict) else None

            if (ch.name == target_color['name'] or ch_rgb == target_color['rgb']):
                return ch

        return None

    def _create_blended_mask(
        self,
        mask: np.ndarray,
        blend_radius: int
    ) -> np.ndarray:
        """
        Create smoothly blended mask for region edges

        Args:
            mask: Binary mask
            blend_radius: Radius for blending in pixels

        Returns:
            Float mask with smooth transitions at edges
        """
        # Convert to float
        mask_float = mask.astype(np.float32)

        if CV2_AVAILABLE:
            # Apply Gaussian blur for smooth transitions
            kernel_size = blend_radius * 2 + 1
            blended = cv2.GaussianBlur(
                mask_float,
                (kernel_size, kernel_size),
                sigma=blend_radius / 2.0
            )
        else:
            # Fallback: scipy gaussian filter
            from scipy.ndimage import gaussian_filter
            blended = gaussian_filter(mask_float, sigma=blend_radius / 2.0)

        return blended

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to hex"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
