"""
region_analyzer.py - Coordinator for AI Call #2 (Region Analysis)

Combines computer vision segmentation with Gemini intelligence
to analyze regions and recommend optimal separation methods.
"""

import numpy as np
from typing import List, Dict, Tuple
import json
from datetime import datetime

from .hybrid_data import (
    ImageRegion, RegionAnalysisResult, RegionType,
    ContentComplexity, HybridSeparationParameters
)
from .separation_data import SeparationMethod
from .region_segmenter import RegionSegmenter
from .gemini_region_prompt import GeminiRegionAnalyzer

# Try to import Gemini API
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Using rule-based fallback.")


class RegionAnalyzer:
    """
    Coordinates AI Call #2 for region-based separation strategy
    Combines computer vision segmentation with Gemini intelligence
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.model = None

        if api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-pro')
            except Exception as e:
                print(f"  [Hybrid AI] Gemini setup error: {e}")
                self.model = None

        self.prompt_builder = GeminiRegionAnalyzer()
        self.region_segmenter = RegionSegmenter()

    def analyze_regions(
        self,
        rgb_image: np.ndarray,
        lab_image: np.ndarray,
        palette,
        analysis_data,
        parameters: HybridSeparationParameters
    ) -> RegionAnalysisResult:
        """
        Complete region analysis workflow

        Step 1: Computer vision segmentation
        Step 2: AI analysis with Gemini
        Step 3: Build structured result

        Args:
            rgb_image: Original RGB image
            lab_image: LAB color space image
            palette: User's color palette
            analysis_data: Results from Analyze unit
            parameters: Hybrid separation parameters

        Returns:
            Complete region analysis with method recommendations
        """

        # ============================================================
        # STEP 1: Computer Vision Segmentation
        # ============================================================
        print("  [Hybrid AI] Step 1: Computer vision segmentation...")

        # Convert analysis_data to dict if it's an object
        analysis_dict = self._extract_analysis_dict(analysis_data)

        preliminary_regions = self.region_segmenter.segment_image(
            rgb_image=rgb_image,
            lab_image=lab_image,
            analysis_data=analysis_dict,
            parameters=parameters
        )

        print(f"  [Hybrid AI] Found {len(preliminary_regions)} preliminary regions")

        # ============================================================
        # STEP 2: AI Analysis with Gemini
        # ============================================================
        if self.model:
            print("  [Hybrid AI] Step 2: AI region analysis with Gemini...")

            ai_analysis = self._get_ai_region_analysis(
                rgb_image=rgb_image,
                preliminary_regions=preliminary_regions,
                palette=palette,
                analysis_data=analysis_dict
            )
        else:
            print("  [Hybrid AI] Step 2: Fallback rule-based analysis (no API key)...")

            ai_analysis = self._get_rule_based_analysis(
                preliminary_regions=preliminary_regions,
                palette=palette,
                analysis_data=analysis_dict
            )

        # ============================================================
        # STEP 3: Build Structured Result
        # ============================================================
        print("  [Hybrid AI] Step 3: Building structured result...")

        result = self._build_region_analysis_result(
            ai_analysis=ai_analysis,
            preliminary_regions=preliminary_regions,
            palette=palette
        )

        print(f"  [Hybrid AI] Analysis complete: {result.region_count} regions identified")

        return result

    def _extract_analysis_dict(self, analysis_data) -> Dict:
        """Extract analysis data into dictionary format"""
        if isinstance(analysis_data, dict):
            return analysis_data

        # Try to extract attributes
        analysis_dict = {}
        if hasattr(analysis_data, 'color_analysis'):
            analysis_dict['color_analysis'] = analysis_data.color_analysis
        if hasattr(analysis_data, 'edge_analysis'):
            analysis_dict['edge_analysis'] = analysis_data.edge_analysis
        if hasattr(analysis_data, 'texture_analysis'):
            analysis_dict['texture_analysis'] = analysis_data.texture_analysis

        return analysis_dict

    def _get_ai_region_analysis(
        self,
        rgb_image: np.ndarray,
        preliminary_regions: List[Dict],
        palette,
        analysis_data: Dict
    ) -> Dict:
        """
        Get AI analysis from Gemini
        """
        # Build prompt
        image_characteristics = {
            'texture_type': analysis_data.get('texture_analysis', {}).get('texture_type', 'mixed'),
            'has_gradients': analysis_data.get('color_analysis', {}).get('gradient_analysis', {}).get('gradient_present', False),
            'edge_type': analysis_data.get('edge_analysis', {}).get('edge_type', 'mixed')
        }

        # Extract palette dict
        palette_dict = self._extract_palette_dict(palette)

        prompt = self.prompt_builder.build_region_analysis_prompt(
            image_characteristics=image_characteristics,
            palette=palette_dict,
            preliminary_regions=preliminary_regions
        )

        # Call Gemini
        try:
            # For now, we'll use text-only mode without image upload
            # Full image upload requires file handling which complicates things
            response = self.model.generate_content(prompt)

            # Parse response
            ai_data = self.prompt_builder.parse_gemini_response(response.text)

            return ai_data

        except Exception as e:
            print(f"  [Hybrid AI] Gemini API error: {e}")
            print("  [Hybrid AI] Falling back to rule-based analysis...")

            return self._get_rule_based_analysis(
                preliminary_regions,
                palette,
                analysis_data
            )

    def _extract_palette_dict(self, palette) -> List[Dict]:
        """Extract palette into list of dicts"""
        palette_list = []

        if hasattr(palette, 'colors'):
            for c in palette.colors:
                palette_list.append({
                    'name': c.name,
                    'rgb': c.rgb,
                    'hex': self._rgb_to_hex(c.rgb)
                })
        else:
            # Assume it's already a list
            palette_list = palette

        return palette_list

    def _get_rule_based_analysis(
        self,
        preliminary_regions: List[Dict],
        palette,
        analysis_data: Dict
    ) -> Dict:
        """
        Fallback rule-based analysis when AI unavailable
        """
        regions = []

        for region in preliminary_regions:
            # Determine method based on characteristics
            edge_sharpness = region['edge_sharpness']
            has_gradients = region['has_gradients']
            texture_score = region['texture_score']
            region_type = region['type']

            # Simple rules
            if region_type == 'vector' or (edge_sharpness > 0.7 and not has_gradients):
                method = SeparationMethod.SPOT_COLOR
                confidence = 0.8
                reasoning = "Sharp edges and flat colors suggest vector content"
            elif region_type == 'photo' or (has_gradients and texture_score > 0.5):
                method = SeparationMethod.SIMULATED_PROCESS
                confidence = 0.75
                reasoning = "Gradients and texture suggest photographic content"
            else:
                method = SeparationMethod.INDEX_COLOR
                confidence = 0.7
                reasoning = "Mixed characteristics work well with index color"

            regions.append({
                'region_id': region['region_id'],
                'content_description': f"{region_type.title()} region",
                'region_type': region_type,
                'complexity': 'moderate',
                'characteristics': {
                    'dominant_colors': [self._rgb_to_hex(c) for c in region['dominant_colors']],
                    'has_gradients': has_gradients,
                    'edge_sharpness': edge_sharpness,
                    'texture_present': texture_score > 0.3
                },
                'recommended_method': method.value,
                'method_confidence': confidence,
                'reasoning': reasoning,
                'priority': 5,
                'alternatives': []
            })

        # Get palette color count
        if hasattr(palette, 'color_count'):
            channel_count = palette.color_count
        elif hasattr(palette, 'colors'):
            channel_count = len(palette.colors)
        else:
            channel_count = len(palette) if isinstance(palette, list) else 4

        return {
            'overall_strategy': f"Rule-based hybrid separation with {len(regions)} regions",
            'complexity_rating': 'moderate',
            'regions': regions,
            'region_interactions': [],
            'expected_results': {
                'quality_rating': 'good',
                'channel_count': channel_count,
                'print_complexity': 'high'
            },
            'confidence_assessment': {
                'overall_confidence': 0.7,
                'uncertainty_areas': ['AI analysis unavailable - using rule-based fallback'],
                'improvement_suggestions': []
            }
        }

    def _build_region_analysis_result(
        self,
        ai_analysis: Dict,
        preliminary_regions: List[Dict],
        palette
    ) -> RegionAnalysisResult:
        """
        Build structured RegionAnalysisResult from AI analysis
        """
        # Build ImageRegion objects
        regions = []
        method_assignments = {}
        confidence_by_region = {}

        for ai_region, prelim_region in zip(ai_analysis['regions'], preliminary_regions):
            region_id = ai_region['region_id']

            # Parse method
            method_str = ai_region['recommended_method']
            method = SeparationMethod(method_str)

            # Parse type
            type_str = ai_region['region_type']
            region_type = RegionType(type_str)

            # Parse complexity
            complexity_str = ai_region['complexity']
            complexity = ContentComplexity(complexity_str)

            # Build ImageRegion
            region = ImageRegion(
                id=region_id,
                region_type=region_type,
                complexity=complexity,
                mask=prelim_region['mask'],
                bounding_box=self._calculate_bounding_box(prelim_region['mask']),
                pixel_count=int(np.sum(prelim_region['mask'])),
                coverage_percentage=float(prelim_region['coverage']),
                dominant_colors=self._hex_to_rgb_list(
                    ai_region['characteristics']['dominant_colors']
                ),
                has_gradients=ai_region['characteristics']['has_gradients'],
                edge_sharpness=float(ai_region['characteristics']['edge_sharpness']),
                texture_score=float(prelim_region['texture_score']),
                recommended_method=method,
                method_confidence=float(ai_region['method_confidence']),
                reasoning=ai_region['reasoning'],
                priority=int(ai_region['priority'])
            )

            regions.append(region)
            method_assignments[region_id] = method
            confidence_by_region[region_id] = ai_region['method_confidence']

        # Build result
        result = RegionAnalysisResult(
            regions=regions,
            region_count=len(regions),
            strategy_summary=ai_analysis['overall_strategy'],
            complexity_rating=ai_analysis['complexity_rating'],
            method_assignments=method_assignments,
            expected_quality=ai_analysis['expected_results']['quality_rating'],
            expected_channels=ai_analysis['expected_results']['channel_count'],
            estimated_processing_time=self._estimate_processing_time(regions),
            overall_confidence=ai_analysis['confidence_assessment']['overall_confidence'],
            confidence_by_region=confidence_by_region,
            gemini_response=ai_analysis,
            timestamp=datetime.now().isoformat()
        )

        return result

    def _calculate_bounding_box(self, mask: np.ndarray) -> Tuple[int, int, int, int]:
        """Calculate bounding box (x, y, width, height) from mask"""
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)

        if not np.any(rows) or not np.any(cols):
            return (0, 0, 0, 0)

        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        return (int(cmin), int(rmin), int(cmax - cmin + 1), int(rmax - rmin + 1))

    def _hex_to_rgb_list(self, hex_colors: List[str]) -> List[Tuple[int, int, int]]:
        """Convert list of hex colors to RGB tuples"""
        rgb_list = []
        for hex_color in hex_colors:
            hex_clean = hex_color.lstrip('#')
            rgb = tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))
            rgb_list.append(rgb)
        return rgb_list

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to hex"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _estimate_processing_time(self, regions: List[ImageRegion]) -> float:
        """Estimate processing time based on regions"""
        base_time = 5.0  # Base overhead

        for region in regions:
            # Add time based on method complexity
            if region.recommended_method == SeparationMethod.SPOT_COLOR:
                base_time += 2.0
            elif region.recommended_method == SeparationMethod.SIMULATED_PROCESS:
                base_time += 10.0
            elif region.recommended_method == SeparationMethod.INDEX_COLOR:
                base_time += 5.0

        return base_time
