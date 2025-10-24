#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SepAI Image Analysis Module
Performs comprehensive image analysis for color separation optimization
"""

import numpy as np
from typing import Optional, List, Tuple
import time
import hashlib

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from scipy import ndimage
    from scipy.cluster.vq import kmeans2
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from .data_structures import (
    ProcessedImageData,
    AnalysisDataModel,
    ColorAnalysisResult,
    EdgeAnalysisResult,
    TextureAnalysisResult,
    ColorCluster,
    ImageDimensions
)


class ColorAnalyzer:
    """Analyzes color characteristics of images"""

    @staticmethod
    def rgb_to_lab(rgb_image: np.ndarray) -> np.ndarray:
        """Convert RGB to LAB color space"""
        if HAS_CV2:
            # OpenCV uses BGR, so we need to convert
            bgr = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
            return lab
        else:
            # Simple approximation without CV2
            # Normalize RGB to 0-1 range
            rgb_norm = rgb_image.astype(np.float32) / 255.0

            # Convert to XYZ
            # Using sRGB to XYZ conversion matrix
            r, g, b = rgb_norm[:, :, 0], rgb_norm[:, :, 1], rgb_norm[:, :, 2]

            # Apply gamma correction
            r = np.where(r > 0.04045, ((r + 0.055) / 1.055) ** 2.4, r / 12.92)
            g = np.where(g > 0.04045, ((g + 0.055) / 1.055) ** 2.4, g / 12.92)
            b = np.where(b > 0.04045, ((b + 0.055) / 1.055) ** 2.4, b / 12.92)

            # XYZ conversion (simplified)
            x = r * 0.4124 + g * 0.3576 + b * 0.1805
            y = r * 0.2126 + g * 0.7152 + b * 0.0722
            z = r * 0.0193 + g * 0.1192 + b * 0.9505

            # XYZ to LAB (simplified, assuming D65 illuminant)
            x = x / 0.95047
            z = z / 1.08883

            # Apply LAB transformation
            def f(t):
                return np.where(t > 0.008856, t ** (1/3), 7.787 * t + 16/116)

            fx = f(x)
            fy = f(y)
            fz = f(z)

            L = 116 * fy - 16
            a = 500 * (fx - fy)
            b_lab = 200 * (fy - fz)

            # Stack and scale to 0-255 range
            lab = np.stack([L * 2.55, a + 128, b_lab + 128], axis=2)
            return np.clip(lab, 0, 255).astype(np.uint8)

    @staticmethod
    def analyze_colors(processed_data: ProcessedImageData, num_clusters: int = 8) -> ColorAnalysisResult:
        """
        Perform comprehensive color analysis

        Args:
            processed_data: Image data to analyze
            num_clusters: Number of color clusters to find

        Returns:
            ColorAnalysisResult with dominant colors and characteristics
        """
        rgb_image = processed_data.rgb_image
        height, width = rgb_image.shape[:2]
        total_pixels = height * width

        # Ensure we have LAB image
        if processed_data.lab_image is None:
            lab_image = ColorAnalyzer.rgb_to_lab(rgb_image)
        else:
            lab_image = processed_data.lab_image

        # Reshape for clustering
        rgb_pixels = rgb_image.reshape(-1, 3)
        lab_pixels = lab_image.reshape(-1, 3).astype(np.float32)

        # Perform color clustering
        clusters = []

        if HAS_SCIPY:
            # Use KMeans clustering for better results
            try:
                centroids, labels = kmeans2(lab_pixels, num_clusters, minit='points')

                for i in range(num_clusters):
                    mask = labels == i
                    pixel_count = np.sum(mask)

                    if pixel_count > 0:
                        # Get RGB centroid
                        rgb_centroid = rgb_pixels[mask].mean(axis=0).astype(int)
                        lab_centroid = centroids[i]

                        # Calculate variance
                        variance = np.var(lab_pixels[mask])

                        percentage = (pixel_count / total_pixels) * 100

                        cluster = ColorCluster(
                            center_rgb=tuple(rgb_centroid),
                            center_lab=tuple(lab_centroid),
                            pixel_count=int(pixel_count),
                            percentage=float(percentage),
                            variance=float(variance),
                            is_dominant=percentage > 5.0
                        )
                        clusters.append(cluster)
            except Exception as e:
                print(f"KMeans clustering failed: {e}, falling back to histogram")

        # Fallback: Simple histogram-based analysis
        if not clusters:
            clusters = ColorAnalyzer._histogram_based_clustering(rgb_pixels, num_clusters, total_pixels)

        # Sort clusters by pixel count
        clusters.sort(key=lambda c: c.pixel_count, reverse=True)

        # Extract dominant colors (top clusters)
        dominant_colors = [c.center_rgb for c in clusters[:min(8, len(clusters))]]

        # Analyze color complexity
        color_complexity = ColorAnalyzer._calculate_complexity(rgb_image)

        # Detect gradients
        has_gradients = ColorAnalyzer._detect_gradients(rgb_image)

        # Count unique colors (sampled for performance)
        sample_size = min(10000, total_pixels)
        sample_indices = np.random.choice(total_pixels, sample_size, replace=False)
        sampled_pixels = rgb_pixels[sample_indices]
        unique_colors = len(np.unique(sampled_pixels.view(np.dtype((np.void, sampled_pixels.dtype.itemsize * 3)))))
        unique_color_ratio = unique_colors / sample_size

        # Estimate recommended color count
        if color_complexity < 0.3 and unique_color_ratio < 0.1:
            color_count_estimate = 2
        elif color_complexity < 0.5 and unique_color_ratio < 0.3:
            color_count_estimate = 4
        elif color_complexity < 0.7:
            color_count_estimate = 6
        else:
            color_count_estimate = 8

        # Determine recommended method
        if has_gradients or color_complexity > 0.7:
            recommended_method = "simulated_process"
        elif len(clusters) <= 4 and color_complexity < 0.4:
            recommended_method = "spot_color"
        elif unique_color_ratio < 0.2:
            recommended_method = "index"
        else:
            recommended_method = "cmyk"

        return ColorAnalysisResult(
            clusters=clusters,
            dominant_colors=dominant_colors,
            color_count_estimate=color_count_estimate,
            color_complexity=color_complexity,
            has_gradients=has_gradients,
            has_fine_details=False,  # Will be set by edge analysis
            recommended_method=recommended_method,
            unique_color_count=int(unique_colors * (total_pixels / sample_size))
        )

    @staticmethod
    def _histogram_based_clustering(rgb_pixels: np.ndarray, num_clusters: int, total_pixels: int) -> List[ColorCluster]:
        """Fallback clustering using histogram quantization"""
        clusters = []

        # Quantize colors to reduce space
        quantized = (rgb_pixels // 32) * 32
        unique_colors, counts = np.unique(quantized.view(np.dtype((np.void, 3))), return_counts=True)

        # Convert back to RGB tuples
        unique_rgb = unique_colors.view(np.uint8).reshape(-1, 3)

        # Sort by count and take top N
        sorted_indices = np.argsort(counts)[::-1]
        top_n = min(num_clusters, len(sorted_indices))

        for i in range(top_n):
            idx = sorted_indices[i]
            rgb = tuple(unique_rgb[idx])
            count = counts[idx]
            percentage = (count / total_pixels) * 100

            cluster = ColorCluster(
                center_rgb=rgb,
                center_lab=(0.0, 0.0, 0.0),  # Simplified
                pixel_count=int(count),
                percentage=float(percentage),
                variance=0.0,
                is_dominant=percentage > 5.0
            )
            clusters.append(cluster)

        return clusters

    @staticmethod
    def _calculate_complexity(rgb_image: np.ndarray) -> float:
        """Calculate color complexity metric (0.0 to 1.0)"""
        # Calculate standard deviation across channels
        std_r = np.std(rgb_image[:, :, 0])
        std_g = np.std(rgb_image[:, :, 1])
        std_b = np.std(rgb_image[:, :, 2])

        avg_std = (std_r + std_g + std_b) / 3.0

        # Normalize to 0-1 range (assuming max std is around 128)
        complexity = min(avg_std / 128.0, 1.0)

        return float(complexity)

    @staticmethod
    def _detect_gradients(rgb_image: np.ndarray) -> bool:
        """Detect if image contains significant gradients"""
        # Convert to grayscale
        gray = np.mean(rgb_image, axis=2).astype(np.uint8)

        if HAS_CV2:
            # Use Sobel edge detection
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        else:
            # Simple gradient approximation
            grad_x = np.diff(gray, axis=1, prepend=0)
            grad_y = np.diff(gray, axis=0, prepend=0)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Check for smooth gradients (moderate gradient values over large areas)
        moderate_gradient = (gradient_magnitude > 5) & (gradient_magnitude < 30)
        gradient_percentage = np.sum(moderate_gradient) / moderate_gradient.size

        return gradient_percentage > 0.2


class EdgeAnalyzer:
    """Analyzes edge and detail characteristics"""

    @staticmethod
    def analyze_edges(processed_data: ProcessedImageData) -> EdgeAnalysisResult:
        """
        Perform edge detection and analysis

        Args:
            processed_data: Image data to analyze

        Returns:
            EdgeAnalysisResult with edge characteristics
        """
        rgb_image = processed_data.rgb_image

        # Convert to grayscale
        gray = np.mean(rgb_image, axis=2).astype(np.uint8)

        if HAS_CV2:
            # Use Canny edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contour_count = len(contours)

            # Calculate edge density
            edge_pixels = np.sum(edges > 0)
            edge_density = edge_pixels / edges.size

            # Analyze edge sharpness using gradient magnitude
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

            # Sharpness is determined by high gradient values
            sharp_edges = gradient_magnitude > 50
            edge_sharpness = np.sum(sharp_edges) / (np.sum(edges > 0) + 1)

        else:
            # Fallback edge detection
            edges = EdgeAnalyzer._simple_edge_detect(gray)
            edge_pixels = np.sum(edges > 0)
            edge_density = edge_pixels / edges.size
            edge_sharpness = 0.5
            contour_count = 0

        # Detect fine lines
        has_fine_lines = edge_density > 0.15

        # Detect halftones (periodic patterns)
        has_halftones = EdgeAnalyzer._detect_halftones(gray)

        # Determine detail level
        if edge_density < 0.05:
            detail_level = "low"
        elif edge_density < 0.15:
            detail_level = "medium"
        else:
            detail_level = "high"

        return EdgeAnalysisResult(
            edge_density=float(edge_density),
            edge_sharpness=float(np.clip(edge_sharpness, 0, 1)),
            has_fine_lines=has_fine_lines,
            has_halftones=has_halftones,
            detail_level=detail_level,
            edge_map=edges if HAS_CV2 else None,
            contour_count=contour_count
        )

    @staticmethod
    def _simple_edge_detect(gray: np.ndarray) -> np.ndarray:
        """Simple edge detection without OpenCV"""
        # Sobel-like kernel
        kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
        kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

        if HAS_SCIPY:
            grad_x = ndimage.convolve(gray.astype(float), kernel_x)
            grad_y = ndimage.convolve(gray.astype(float), kernel_y)
        else:
            # Very basic gradient
            grad_x = np.diff(gray, axis=1, prepend=0)
            grad_y = np.diff(gray, axis=0, prepend=0)

        gradient = np.sqrt(grad_x**2 + grad_y**2)
        edges = (gradient > 30).astype(np.uint8) * 255

        return edges

    @staticmethod
    def _detect_halftones(gray: np.ndarray) -> bool:
        """Detect halftone patterns using frequency analysis"""
        # Sample a region for performance
        h, w = gray.shape
        sample_size = 256
        if h > sample_size and w > sample_size:
            sample = gray[:sample_size, :sample_size]
        else:
            sample = gray

        # Simple variance check for periodic patterns
        # Halftones typically have moderate variance with regular patterns
        variance = np.var(sample)

        # Check for periodic structure (simplified)
        if HAS_SCIPY:
            # Use FFT to detect periodic patterns
            fft = np.fft.fft2(sample)
            fft_magnitude = np.abs(fft)

            # Exclude DC component
            fft_magnitude[0, 0] = 0

            # Check for strong frequency components (indicating periodicity)
            threshold = np.mean(fft_magnitude) + 2 * np.std(fft_magnitude)
            periodic_peaks = np.sum(fft_magnitude > threshold)

            return periodic_peaks > 10 and variance > 100
        else:
            # Fallback: just use variance
            return 500 < variance < 3000


class TextureAnalyzer:
    """Analyzes texture and pattern characteristics"""

    @staticmethod
    def analyze_texture(processed_data: ProcessedImageData) -> TextureAnalysisResult:
        """
        Perform texture analysis

        Args:
            processed_data: Image data to analyze

        Returns:
            TextureAnalysisResult with texture characteristics
        """
        rgb_image = processed_data.rgb_image
        gray = np.mean(rgb_image, axis=2).astype(np.uint8)

        # Calculate texture complexity using local variance
        texture_complexity = TextureAnalyzer._calculate_texture_complexity(gray)

        # Detect noise level
        noise_level = TextureAnalyzer._estimate_noise(gray)

        # Determine grain size
        if texture_complexity < 0.2:
            grain_size = "none"
        elif texture_complexity < 0.4:
            grain_size = "fine"
        elif texture_complexity < 0.7:
            grain_size = "medium"
        else:
            grain_size = "coarse"

        # Detect screening patterns
        has_screens = noise_level > 0.3 and texture_complexity > 0.4

        # Identify dominant patterns (simplified)
        dominant_patterns = []
        if has_screens:
            dominant_patterns.append("halftone")
        if texture_complexity > 0.6:
            dominant_patterns.append("textured")
        if noise_level > 0.4:
            dominant_patterns.append("noisy")

        return TextureAnalysisResult(
            texture_complexity=float(texture_complexity),
            dominant_patterns=dominant_patterns,
            noise_level=float(noise_level),
            grain_size=grain_size,
            has_screens=has_screens
        )

    @staticmethod
    def _calculate_texture_complexity(gray: np.ndarray) -> float:
        """Calculate texture complexity using local variance"""
        if HAS_SCIPY:
            # Use local standard deviation as texture measure
            local_std = ndimage.generic_filter(gray.astype(float), np.std, size=5)
            complexity = np.mean(local_std) / 128.0
        else:
            # Simplified: global variance
            complexity = np.std(gray) / 128.0

        return float(np.clip(complexity, 0, 1))

    @staticmethod
    def _estimate_noise(gray: np.ndarray) -> float:
        """Estimate noise level in image"""
        if HAS_SCIPY:
            # Use Laplacian variance as noise estimate
            laplacian = ndimage.laplace(gray.astype(float))
            noise = np.var(laplacian) / 10000.0
        else:
            # Simplified noise estimation
            diff = np.diff(gray.astype(float), axis=1)
            noise = np.std(diff) / 128.0

        return float(np.clip(noise, 0, 1))


class AnalyzeUnitCoordinator:
    """Coordinates all analysis operations"""

    def __init__(self):
        self.color_analyzer = ColorAnalyzer()
        self.edge_analyzer = EdgeAnalyzer()
        self.texture_analyzer = TextureAnalyzer()

    def process(self, processed_data: ProcessedImageData) -> AnalysisDataModel:
        """
        Run complete analysis pipeline

        Args:
            processed_data: Image data to analyze

        Returns:
            Complete analysis results
        """
        # Generate cache key
        cache_key = self._generate_cache_key(processed_data)

        # Perform analyses
        color_analysis = self.color_analyzer.analyze_colors(processed_data)
        edge_analysis = self.edge_analyzer.analyze_edges(processed_data)
        texture_analysis = self.texture_analyzer.analyze_texture(processed_data)

        # Update color analysis with edge information
        color_analysis.has_fine_details = edge_analysis.detail_level == "high"

        # Create complete analysis model
        analysis_model = AnalysisDataModel(
            image_dimensions=processed_data.dimensions,
            color_analysis=color_analysis,
            edge_analysis=edge_analysis,
            texture_analysis=texture_analysis,
            analysis_timestamp=time.time(),
            cache_key=cache_key
        )

        return analysis_model

    def _generate_cache_key(self, processed_data: ProcessedImageData) -> str:
        """Generate unique cache key for image data"""
        # Use image dimensions and sample pixels for hash
        dims = processed_data.dimensions
        key_string = f"{dims.original_width}x{dims.original_height}"

        # Add sample of pixel data
        if processed_data.rgb_image is not None:
            sample = processed_data.rgb_image[::10, ::10].tobytes()[:1000]
            key_string += sample.hex()

        return hashlib.md5(key_string.encode()).hexdigest()


# Convenience function for direct use
def analyze_image(image_data: np.ndarray, dimensions: Optional[ImageDimensions] = None) -> AnalysisDataModel:
    """
    Convenience function to analyze an image

    Args:
        image_data: RGB image as numpy array
        dimensions: Optional image dimensions

    Returns:
        Complete analysis results
    """
    processed_data = ProcessedImageData(
        rgb_image=image_data,
        dimensions=dimensions
    )

    # Convert to LAB if possible
    if HAS_CV2:
        processed_data.lab_image = ColorAnalyzer.rgb_to_lab(image_data)

    analyzer = AnalyzeUnitCoordinator()
    return analyzer.process(processed_data)
