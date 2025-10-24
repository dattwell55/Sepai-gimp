"""
region_segmenter.py - Image segmentation for hybrid separation

Performs initial image segmentation before AI analysis using multiple
computer vision techniques: edge-based, color-based, and texture-based.
"""

import numpy as np
from typing import List, Dict, Tuple
from scipy import ndimage

from .hybrid_data import HybridSeparationParameters

# Try to import CV libraries
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python not installed. Region segmentation will be limited.")

try:
    from skimage.segmentation import slic
    from skimage.feature import canny
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False
    print("Warning: scikit-image not installed. Using fallback segmentation.")


class RegionSegmenter:
    """
    Performs initial image segmentation before AI analysis
    Uses multiple CV techniques combined
    """

    def segment_image(
        self,
        rgb_image: np.ndarray,
        lab_image: np.ndarray,
        analysis_data: Dict,
        parameters: HybridSeparationParameters
    ) -> List[Dict]:
        """
        Perform initial segmentation

        Args:
            rgb_image: RGB image array
            lab_image: LAB color space image
            analysis_data: Analysis data from Analyze unit
            parameters: Hybrid separation parameters

        Returns:
            List of preliminary region dictionaries
        """
        height, width = rgb_image.shape[:2]

        print(f"    [Segmenter] Image size: {width}x{height}")

        # Technique 1: Edge-based segmentation
        edge_regions = self._segment_by_edges(
            lab_image,
            analysis_data,
            parameters.edge_sensitivity
        )

        # Technique 2: Color-based segmentation
        color_regions = self._segment_by_color(
            lab_image,
            min_region_size=parameters.min_region_size
        )

        # Technique 3: Texture-based segmentation
        texture_regions = self._segment_by_texture(
            rgb_image,
            analysis_data
        )

        # Combine techniques
        combined_regions = self._combine_segmentations(
            edge_regions,
            color_regions,
            texture_regions,
            image_shape=(height, width)
        )

        # Filter small regions
        filtered_regions = self._filter_small_regions(
            combined_regions,
            min_size=parameters.min_region_size
        )

        # Calculate region characteristics
        characterized_regions = self._characterize_regions(
            filtered_regions,
            rgb_image,
            lab_image,
            analysis_data
        )

        print(f"    [Segmenter] Identified {len(characterized_regions)} regions")

        return characterized_regions

    def _segment_by_edges(
        self,
        lab_image: np.ndarray,
        analysis_data: Dict,
        sensitivity: float
    ) -> List[np.ndarray]:
        """
        Segment based on edge detection
        Sharp edges suggest vector content
        """
        L_channel = lab_image[:, :, 0]

        if SKIMAGE_AVAILABLE:
            # Multi-scale edge detection
            edges_fine = canny(L_channel, sigma=1.0)
            edges_coarse = canny(L_channel, sigma=3.0)

            # Combine
            edges_combined = edges_fine | edges_coarse
        else:
            # Fallback: simple gradient-based edges
            edges_combined = self._simple_edge_detection(L_channel)

        if CV2_AVAILABLE:
            # Dilate to create regions
            kernel_size = int(10 * sensitivity)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            edges_dilated = cv2.dilate(edges_combined.astype(np.uint8), kernel)
        else:
            # Fallback: scipy dilation
            kernel_size = int(10 * sensitivity)
            edges_dilated = ndimage.binary_dilation(
                edges_combined,
                iterations=kernel_size // 2
            ).astype(np.uint8)

        # Label connected components
        labeled, num_regions = ndimage.label(edges_dilated)

        regions = []
        for i in range(1, num_regions + 1):
            mask = (labeled == i)
            if np.sum(mask) > 100:  # Minimum size
                regions.append(mask)

        return regions

    def _simple_edge_detection(self, L_channel: np.ndarray) -> np.ndarray:
        """Fallback edge detection using gradients"""
        # Calculate gradients
        grad_y, grad_x = np.gradient(L_channel)
        gradient_mag = np.sqrt(grad_x**2 + grad_y**2)

        # Threshold
        threshold = np.percentile(gradient_mag, 75)
        edges = gradient_mag > threshold

        return edges

    def _segment_by_color(
        self,
        lab_image: np.ndarray,
        min_region_size: int
    ) -> List[np.ndarray]:
        """
        Segment based on color similarity using SLIC superpixels
        """
        if not SKIMAGE_AVAILABLE:
            # Fallback: simple k-means-like clustering
            return self._simple_color_segmentation(lab_image, min_region_size)

        # SLIC superpixel segmentation
        n_segments = max(10, (lab_image.shape[0] * lab_image.shape[1]) // 10000)

        segments = slic(
            lab_image,
            n_segments=n_segments,
            compactness=10.0,
            sigma=1.0,
            start_label=1
        )

        # Convert superpixels to regions
        regions = []
        for seg_id in np.unique(segments):
            if seg_id == 0:
                continue
            mask = (segments == seg_id)
            if np.sum(mask) >= min_region_size:
                regions.append(mask)

        return regions

    def _simple_color_segmentation(
        self,
        lab_image: np.ndarray,
        min_region_size: int
    ) -> List[np.ndarray]:
        """Fallback color segmentation"""
        # Quantize LAB values into buckets
        L_quant = (lab_image[:, :, 0] // 20).astype(int)
        A_quant = ((lab_image[:, :, 1] + 128) // 40).astype(int)
        B_quant = ((lab_image[:, :, 2] + 128) // 40).astype(int)

        # Combine into single label
        labels = L_quant * 100 + A_quant * 10 + B_quant

        # Label connected components for each color
        regions = []
        for label_val in np.unique(labels):
            mask = (labels == label_val)
            if np.sum(mask) >= min_region_size:
                # Label connected components within this color
                labeled, num = ndimage.label(mask)
                for i in range(1, num + 1):
                    component_mask = (labeled == i)
                    if np.sum(component_mask) >= min_region_size:
                        regions.append(component_mask)

        return regions

    def _segment_by_texture(
        self,
        rgb_image: np.ndarray,
        analysis_data: Dict
    ) -> List[np.ndarray]:
        """
        Segment based on texture characteristics
        Photo regions have texture, vector regions don't
        """
        if CV2_AVAILABLE:
            gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
        else:
            # Convert to grayscale manually
            gray = np.dot(rgb_image[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)

        # Calculate local standard deviation (texture measure)
        window_size = 15
        kernel = np.ones((window_size, window_size)) / (window_size ** 2)

        if CV2_AVAILABLE:
            mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
            sqr_mean = cv2.filter2D((gray ** 2).astype(np.float32), -1, kernel)
        else:
            # Fallback: scipy convolve
            from scipy.ndimage import convolve
            mean = convolve(gray.astype(np.float32), kernel, mode='reflect')
            sqr_mean = convolve((gray ** 2).astype(np.float32), kernel, mode='reflect')

        variance = sqr_mean - (mean ** 2)
        std_dev = np.sqrt(np.maximum(variance, 0))

        # Threshold to identify textured regions
        texture_threshold = np.percentile(std_dev, 60)
        textured_mask = std_dev > texture_threshold
        smooth_mask = ~textured_mask

        return [textured_mask, smooth_mask]

    def _combine_segmentations(
        self,
        edge_regions: List[np.ndarray],
        color_regions: List[np.ndarray],
        texture_regions: List[np.ndarray],
        image_shape: Tuple[int, int]
    ) -> List[np.ndarray]:
        """
        Intelligently combine multiple segmentation results
        """
        # Voting-based combination
        height, width = image_shape
        vote_map = np.zeros((height, width), dtype=np.int32)

        # Create region ID map
        region_id = 1
        combined = []

        # Process edge regions (high priority)
        for mask in edge_regions:
            if np.sum(mask) > 500:  # Minimum size
                combined.append(mask)
                vote_map[mask] = region_id
                region_id += 1

        # Fill in with color regions where no edge regions exist
        for mask in color_regions:
            if np.sum(mask) > 500:
                # Only where not already assigned
                unassigned = (vote_map == 0) & mask
                if np.sum(unassigned) > 500:
                    combined.append(unassigned)
                    vote_map[unassigned] = region_id
                    region_id += 1

        # If we have very few regions, fill remaining with texture
        if len(combined) < 2:
            for mask in texture_regions:
                unassigned = (vote_map == 0) & mask
                if np.sum(unassigned) > 1000:
                    combined.append(unassigned)
                    vote_map[unassigned] = region_id
                    region_id += 1

        return combined

    def _filter_small_regions(
        self,
        regions: List[np.ndarray],
        min_size: int
    ) -> List[np.ndarray]:
        """Remove regions smaller than threshold"""
        return [r for r in regions if np.sum(r) >= min_size]

    def _characterize_regions(
        self,
        regions: List[np.ndarray],
        rgb_image: np.ndarray,
        lab_image: np.ndarray,
        analysis_data: Dict
    ) -> List[Dict]:
        """
        Calculate characteristics for each region
        """
        characterized = []

        for idx, mask in enumerate(regions):
            # Extract region pixels
            region_rgb = rgb_image[mask]
            region_lab = lab_image[mask]

            # Calculate characteristics
            characteristics = {
                'region_id': f'region_{idx + 1}',
                'mask': mask,
                'coverage': (np.sum(mask) / mask.size) * 100,

                # Color analysis
                'unique_colors': len(np.unique(region_rgb.reshape(-1, 3), axis=0)),
                'dominant_colors': self._get_dominant_colors(region_rgb, n=3),
                'color_variance': float(np.var(region_lab)),

                # Edge analysis
                'edge_sharpness': self._calculate_edge_sharpness(mask, lab_image),

                # Gradient detection
                'has_gradients': self._detect_gradients_in_region(region_lab),

                # Texture
                'texture_score': self._calculate_texture_score(region_rgb),

                # Preliminary type guess
                'type': self._guess_region_type(mask, rgb_image, lab_image)
            }

            characterized.append(characteristics)

        return characterized

    def _get_dominant_colors(
        self,
        region_pixels: np.ndarray,
        n: int = 3
    ) -> List[Tuple[int, int, int]]:
        """Get top N dominant colors in region"""
        # Reshape to 2D array of pixels
        pixels = region_pixels.reshape(-1, 3)

        # Simple approach: bin colors and find most common
        # Quantize to reduce number of unique colors
        quantized = (pixels // 32) * 32  # Reduce to ~8 values per channel

        # Find unique colors and counts
        unique_colors, counts = np.unique(quantized, axis=0, return_counts=True)

        # Sort by count
        sorted_indices = np.argsort(counts)[::-1]

        # Return top N
        top_n = min(n, len(unique_colors))
        dominant = [tuple(unique_colors[sorted_indices[i]].astype(int)) for i in range(top_n)]

        return dominant

    def _calculate_edge_sharpness(
        self,
        mask: np.ndarray,
        lab_image: np.ndarray
    ) -> float:
        """
        Calculate average edge sharpness in region
        Returns 0-1, higher = sharper edges
        """
        L_channel = lab_image[:, :, 0]

        if CV2_AVAILABLE:
            # Calculate gradient in region
            grad_x = cv2.Sobel(L_channel, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(L_channel, cv2.CV_64F, 0, 1, ksize=3)
        else:
            # Fallback: numpy gradient
            grad_y, grad_x = np.gradient(L_channel)

        gradient_mag = np.sqrt(grad_x**2 + grad_y**2)

        # Average gradient in region
        region_gradient = gradient_mag[mask]
        avg_gradient = np.mean(region_gradient)

        # Normalize to 0-1
        return min(1.0, avg_gradient / 50.0)

    def _detect_gradients_in_region(
        self,
        region_lab: np.ndarray
    ) -> bool:
        """
        Detect if region contains gradients
        """
        L_channel = region_lab[:, 0]

        # Check for smooth transitions (gradients)
        L_sorted = np.sort(L_channel)
        differences = np.diff(L_sorted)

        # Gradients have many small, consistent differences
        small_diffs = differences < 5
        gradient_ratio = np.sum(small_diffs) / max(1, len(differences))

        return gradient_ratio > 0.7

    def _calculate_texture_score(
        self,
        region_pixels: np.ndarray
    ) -> float:
        """
        Calculate texture complexity score 0-1
        Higher = more texture/detail
        """
        # Convert to grayscale
        if len(region_pixels.shape) == 2:
            gray = region_pixels
        else:
            gray = np.dot(region_pixels[..., :3], [0.299, 0.587, 0.114])

        # Calculate local standard deviation
        std_dev = np.std(gray)

        # Normalize to 0-1
        return min(1.0, std_dev / 30.0)

    def _guess_region_type(
        self,
        mask: np.ndarray,
        rgb_image: np.ndarray,
        lab_image: np.ndarray
    ) -> str:
        """
        Make preliminary guess about region type
        Will be refined by Gemini
        """
        # Extract region
        region_rgb = rgb_image[mask]
        region_lab = lab_image[mask]

        # Calculate metrics
        edge_sharpness = self._calculate_edge_sharpness(mask, lab_image)
        has_gradients = self._detect_gradients_in_region(region_lab)
        texture_score = self._calculate_texture_score(region_rgb)
        unique_colors = len(np.unique(region_rgb.reshape(-1, 3), axis=0))

        # Decision logic
        if edge_sharpness > 0.7 and not has_gradients and unique_colors < 10:
            return "vector"
        elif texture_score > 0.6 and has_gradients:
            return "photo"
        elif edge_sharpness > 0.8 and unique_colors < 3:
            return "text"
        else:
            return "mixed"
