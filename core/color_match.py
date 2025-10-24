#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Color Match Module - AI-Powered Palette Generation
Integrates with Gemini AI for intelligent color palette creation
"""

import json
import requests
from typing import Dict, List, Optional, Tuple
import time

# Import analysis data structures
from .data_structures import AnalysisDataModel

# Import prompt builder
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts.palette_generation import (
    build_gemini_prompt,
    parse_gemini_response,
    validate_palette,
    GEMINI_CONFIG
)


class GeminiPaletteGenerator:
    """Generates color palettes using Gemini AI"""

    def __init__(self, api_key: str):
        """
        Initialize Gemini palette generator

        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = GEMINI_CONFIG['model']

    def generate_palette(
        self,
        analysis_data: AnalysisDataModel,
        target_count: int,
        user_preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Generate palette using Gemini AI

        Args:
            analysis_data: Complete analysis results
            target_count: Desired number of colors (2-24)
            user_preferences: Optional user constraints

        Returns:
            Dictionary with palette and recommendations
        """
        try:
            # Build comprehensive prompt
            prompt = build_gemini_prompt(
                color_analysis=analysis_data.color_analysis.to_dict(),
                edge_analysis=analysis_data.edge_analysis.to_dict(),
                texture_analysis=analysis_data.texture_analysis.to_dict(),
                target_count=target_count,
                user_preferences=user_preferences
            )

            # Call Gemini API
            response_text = self._call_gemini_api(prompt)

            if not response_text:
                return {
                    'error': True,
                    'message': 'No response from Gemini API'
                }

            # Parse response
            palette_data = parse_gemini_response(response_text)

            if not palette_data:
                return {
                    'error': True,
                    'message': 'Failed to parse Gemini response',
                    'raw_response': response_text
                }

            # Validate palette
            warnings = validate_palette(palette_data, target_count)

            # Add metadata
            palette_data['validation_warnings'] = warnings
            palette_data['generation_timestamp'] = time.time()
            palette_data['target_count'] = target_count

            return palette_data

        except Exception as e:
            return {
                'error': True,
                'message': f'Palette generation failed: {str(e)}'
            }

    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """
        Call Gemini API with prompt

        Args:
            prompt: Formatted prompt text

        Returns:
            Response text or None on error
        """
        try:
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": GEMINI_CONFIG['temperature'],
                    "topP": GEMINI_CONFIG['top_p'],
                    "topK": GEMINI_CONFIG['top_k'],
                    "maxOutputTokens": GEMINI_CONFIG['max_output_tokens'],
                }
            }

            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract text from response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        return parts[0]['text']

            return None

        except requests.exceptions.RequestException as e:
            print(f"Gemini API request error: {e}")
            return None
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None


class PaletteManager:
    """Manages palette operations with undo/redo support"""

    def __init__(self):
        """Initialize palette manager"""
        self.palette = []
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 50

    def set_palette(self, palette: List[Dict]):
        """
        Set current palette and save to undo stack

        Args:
            palette: List of color dictionaries
        """
        # Save current state to undo stack
        if self.palette:
            self.undo_stack.append(self.palette.copy())
            # Limit history size
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)

        self.palette = palette.copy()
        self.redo_stack.clear()

    def get_palette(self) -> List[Dict]:
        """Get current palette"""
        return self.palette.copy()

    def add_color(self, color: Dict):
        """
        Add color to palette

        Args:
            color: Color dictionary with rgb, name, etc.
        """
        self.set_palette(self.palette + [color])

    def remove_color(self, index: int):
        """
        Remove color at index

        Args:
            index: Index of color to remove
        """
        if 0 <= index < len(self.palette):
            new_palette = self.palette.copy()
            new_palette.pop(index)
            self.set_palette(new_palette)

    def replace_color(self, index: int, new_color: Dict):
        """
        Replace color at index

        Args:
            index: Index of color to replace
            new_color: New color dictionary
        """
        if 0 <= index < len(self.palette):
            new_palette = self.palette.copy()
            new_palette[index] = new_color
            self.set_palette(new_palette)

    def undo(self) -> bool:
        """
        Undo last change

        Returns:
            True if undo was performed
        """
        if not self.undo_stack:
            return False

        # Save current to redo stack
        self.redo_stack.append(self.palette.copy())

        # Restore from undo stack
        self.palette = self.undo_stack.pop()

        return True

    def redo(self) -> bool:
        """
        Redo last undone change

        Returns:
            True if redo was performed
        """
        if not self.redo_stack:
            return False

        # Save current to undo stack
        self.undo_stack.append(self.palette.copy())

        # Restore from redo stack
        self.palette = self.redo_stack.pop()

        return True

    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self.redo_stack) > 0

    def clear_history(self):
        """Clear undo/redo history"""
        self.undo_stack.clear()
        self.redo_stack.clear()


class ColorMatchCoordinator:
    """Coordinates color matching workflow"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize coordinator

        Args:
            api_key: Optional Gemini API key
        """
        self.api_key = api_key
        self.gemini_generator = GeminiPaletteGenerator(api_key) if api_key else None
        self.palette_manager = PaletteManager()
        self.analysis_data = None

    def set_analysis_data(self, analysis_data: AnalysisDataModel):
        """
        Set analysis data for palette generation

        Args:
            analysis_data: Complete analysis results
        """
        self.analysis_data = analysis_data

    def generate_palette_with_ai(
        self,
        target_count: int,
        user_preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Generate palette using AI

        Args:
            target_count: Desired number of colors
            user_preferences: Optional user constraints

        Returns:
            Generation results
        """
        if not self.gemini_generator:
            return {
                'error': True,
                'message': 'Gemini API key not configured'
            }

        if not self.analysis_data:
            return {
                'error': True,
                'message': 'No analysis data available'
            }

        result = self.gemini_generator.generate_palette(
            self.analysis_data,
            target_count,
            user_preferences
        )

        # If successful, update palette manager
        if not result.get('error'):
            palette = result.get('palette', [])
            self.palette_manager.set_palette(palette)

        return result

    def generate_palette_from_analysis(self, target_count: int) -> List[Dict]:
        """
        Generate palette directly from analysis (no AI)

        Args:
            target_count: Desired number of colors

        Returns:
            List of color dictionaries
        """
        if not self.analysis_data:
            return []

        # Use dominant colors from analysis
        clusters = self.analysis_data.color_analysis.clusters[:target_count]

        palette = []
        for i, cluster in enumerate(clusters):
            color = {
                'name': f"Color {i + 1}",
                'rgb': list(cluster.center_rgb),
                'pantone_match': None,
                'halftone_angle': 45 + (i * 15) % 90,
                'suggested_frequency': 55,
                'coverage_estimate': cluster.percentage / 100.0,
                'layer_order': i + 1,
                'reasoning': f"Dominant color covering {cluster.percentage:.1f}% of image"
            }
            palette.append(color)

        self.palette_manager.set_palette(palette)
        return palette

    def get_current_palette(self) -> List[Dict]:
        """Get current palette"""
        return self.palette_manager.get_palette()

    def modify_palette(self, action: str, **kwargs):
        """
        Modify current palette

        Args:
            action: 'add', 'remove', or 'replace'
            **kwargs: Action-specific arguments
        """
        if action == 'add':
            self.palette_manager.add_color(kwargs['color'])
        elif action == 'remove':
            self.palette_manager.remove_color(kwargs['index'])
        elif action == 'replace':
            self.palette_manager.replace_color(kwargs['index'], kwargs['color'])

    def undo(self) -> bool:
        """Undo last palette change"""
        return self.palette_manager.undo()

    def redo(self) -> bool:
        """Redo last undone change"""
        return self.palette_manager.redo()

    def can_undo(self) -> bool:
        """Check if undo is available"""
        return self.palette_manager.can_undo()

    def can_redo(self) -> bool:
        """Check if redo is available"""
        return self.palette_manager.can_redo()


# Convenience function for quick palette generation
def generate_palette(
    analysis_data: AnalysisDataModel,
    target_count: int,
    api_key: Optional[str] = None,
    use_ai: bool = True
) -> Dict:
    """
    Generate color palette

    Args:
        analysis_data: Analysis results
        target_count: Number of colors desired
        api_key: Optional Gemini API key
        use_ai: Whether to use AI (requires api_key)

    Returns:
        Palette generation results
    """
    coordinator = ColorMatchCoordinator(api_key)
    coordinator.set_analysis_data(analysis_data)

    if use_ai and api_key:
        return coordinator.generate_palette_with_ai(target_count)
    else:
        palette = coordinator.generate_palette_from_analysis(target_count)
        return {
            'palette': palette,
            'overall_strategy': 'Generated from dominant color clusters',
            'confidence_score': 0.7
        }
