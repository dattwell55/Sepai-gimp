"""
method_analyzer.py - AI Call #1: Method recommendation
Phase 2: AI-powered separation method selection
"""

import json
import re
from typing import Dict, List

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Using rule-based fallback.")

from .separation_data import SeparationMethod, MethodRecommendation


class AIMethodAnalyzer:
    """
    AI-powered method recommendation system
    Uses Gemini to analyze image + palette and suggest best approach
    """

    def __init__(self, api_key: str = None):
        """
        Initialize analyzer with optional Gemini API key

        Args:
            api_key: Google Gemini API key (optional)
        """
        self.api_key = api_key
        self.model = None

        if api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                print("  [AI] Gemini API initialized")
            except Exception as e:
                print(f"  [AI] Gemini initialization failed: {e}")
                self.model = None
        else:
            print("  [AI] Using rule-based recommendations (no API key)")

    def analyze_and_recommend(
        self,
        analysis_data: Dict,
        palette_data: Dict
    ) -> Dict:
        """
        Main AI analysis: Recommend separation methods

        Args:
            analysis_data: Results from Analyze unit
            palette_data: Palette from Color Match unit

        Returns:
            Dictionary with recommendations:
            {
                'recommended': MethodRecommendation,
                'alternatives': List[MethodRecommendation],
                'all_methods': List[MethodRecommendation]
            }
        """
        # Build context for AI
        context = self._build_analysis_context(
            analysis_data,
            palette_data
        )

        # If AI available, get recommendation
        if self.model:
            print("  [AI] Analyzing with Gemini...")
            ai_recommendations = self._get_ai_recommendations(context)
        else:
            print("  [AI] Using rule-based analysis...")
            ai_recommendations = self._get_rule_based_recommendations(context)

        # Score and rank all methods
        scored_methods = self._score_all_methods(context, ai_recommendations)

        return {
            'recommended': scored_methods[0] if scored_methods else None,
            'alternatives': scored_methods[1:3] if len(scored_methods) > 1 else [],
            'all_methods': scored_methods
        }

    def _build_analysis_context(
        self,
        analysis_data: Dict,
        palette_data: Dict
    ) -> Dict:
        """Build context dictionary for method evaluation"""
        # Handle different palette data structures
        if isinstance(palette_data, dict):
            colors = palette_data.get('colors', [])
        elif isinstance(palette_data, list):
            colors = palette_data
        else:
            colors = []

        return {
            'color_count': len(colors),
            'palette_colors': colors,
            'image_characteristics': {
                'edge_type': analysis_data.get('edge_analysis', {}).get('edge_type', 'mixed'),
                'has_gradients': analysis_data.get('color_analysis', {}).get('gradient_present', False),
                'texture_type': analysis_data.get('texture_analysis', {}).get('texture_type', 'mixed'),
                'line_work_score': analysis_data.get('edge_analysis', {}).get('line_work_score', 0.5),
                'total_colors': analysis_data.get('color_analysis', {}).get('total_unique_colors', 0),
                'complexity': analysis_data.get('color_analysis', {}).get('complexity_score', 0.5)
            }
        }

    def _get_ai_recommendations(self, context: Dict) -> Dict:
        """
        Use Gemini AI to analyze and recommend methods

        This is AI CALL #1
        """
        prompt = self._build_recommendation_prompt(context)

        try:
            response = self.model.generate_content(prompt)
            return self._parse_ai_response(response.text)
        except Exception as e:
            print(f"  [AI] Gemini API error: {e}")
            print("  [AI] Falling back to rule-based...")
            return self._get_rule_based_recommendations(context)

    def _build_recommendation_prompt(self, context: Dict) -> str:
        """Build prompt for Gemini AI method recommendation"""

        # Format palette summary
        palette_colors = context['palette_colors'][:3]  # Show first 3
        palette_summary = f"{context['color_count']} colors: "

        if palette_colors:
            color_strs = []
            for c in palette_colors:
                name = c.get('name', 'Unnamed')
                rgb = c.get('rgb', [0, 0, 0])
                color_strs.append(f"{name} (RGB: {rgb})")
            palette_summary += ", ".join(color_strs)

            if context['color_count'] > 3:
                palette_summary += f", and {context['color_count'] - 3} more"
        else:
            palette_summary += "No colors"

        chars = context['image_characteristics']

        prompt = f"""You are an expert screen printing color separation advisor. Analyze this image and recommend the best separation method.

IMAGE CHARACTERISTICS:
- Palette: {palette_summary}
- Edge Type: {chars['edge_type']}
- Has Gradients: {chars['has_gradients']}
- Texture Type: {chars['texture_type']}
- Line Work Score: {chars['line_work_score']:.2f}
- Total Unique Colors: {chars['total_colors']}
- Complexity: {chars['complexity']:.2f}

AVAILABLE SEPARATION METHODS:
1. SPOT COLOR - Best for 2-6 flat colors, sharp edges, logos/graphics
2. SIMULATED PROCESS - Best for photos, gradients, 4-12 colors
3. INDEX COLOR - Best for 6-12 colors, moderate complexity
4. CMYK - Standard 4-color process (always available)
5. RGB - Simple fallback (rarely recommended)
6. HYBRID AI - Advanced region-based separation (complex images)

Analyze the image characteristics and recommend:
1. The BEST method (primary recommendation)
2. TWO alternative methods
3. For each method, provide:
   - Score (0-100)
   - Confidence (0-1)
   - Brief reasoning (2-3 sentences)
   - Key strengths (3-4 points)
   - Limitations (2-3 points)
   - Expected channel count
   - Quality rating (excellent/good/fair)

Respond in JSON format:
{{
  "recommended": {{
    "method": "spot_color",
    "score": 95,
    "confidence": 0.95,
    "reasoning": "...",
    "strengths": ["...", "..."],
    "limitations": ["..."],
    "expected_channels": 4,
    "quality": "excellent"
  }},
  "alternatives": [
    {{ similar structure }},
    {{ similar structure }}
  ]
}}
"""
        return prompt

    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse Gemini's JSON response"""
        try:
            # Extract JSON from response (may be wrapped in markdown)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data
            else:
                print("  [AI] No JSON found in response")
                return {}
        except json.JSONDecodeError as e:
            print(f"  [AI] JSON parse error: {e}")
            return {}

    def _get_rule_based_recommendations(self, context: Dict) -> Dict:
        """Fallback rule-based recommendations when AI unavailable"""

        color_count = context['color_count']
        chars = context['image_characteristics']

        # Simple rule-based scoring
        if color_count <= 6 and chars['edge_type'] == 'sharp' and not chars['has_gradients']:
            primary = 'spot_color'
            score = 90
            reasoning = 'Few colors with sharp edges ideal for spot color separation'
            strengths = ['Crisp edges', 'Accurate color matching', 'Cost-effective']
            limitations = ['Cannot handle gradients well']
        elif chars['texture_type'] == 'photo' and chars['has_gradients']:
            primary = 'simulated_process'
            score = 85
            reasoning = 'Photo texture and gradients work best with simulated process'
            strengths = ['Smooth gradients', 'Photorealistic quality', 'Good detail']
            limitations = ['More complex printing', 'Higher cost']
        elif 6 <= color_count <= 12:
            primary = 'index_color'
            score = 80
            reasoning = 'Moderate color count balanced with index color separation'
            strengths = ['Good quality/cost balance', 'Handles moderate complexity']
            limitations = ['May show banding in gradients']
        else:
            primary = 'simulated_process'
            score = 75
            reasoning = 'Complex image best handled by simulated process'
            strengths = ['Handles complexity well', 'Good overall quality']
            limitations = ['Higher printing cost']

        return {
            'recommended': {
                'method': primary,
                'score': score,
                'confidence': 0.75,
                'reasoning': reasoning,
                'strengths': strengths,
                'limitations': limitations,
                'expected_channels': min(color_count, 8),
                'quality': 'good'
            },
            'alternatives': [
                {
                    'method': 'cmyk',
                    'score': 65,
                    'confidence': 0.7,
                    'reasoning': 'Standard CMYK always available as fallback',
                    'strengths': ['Industry standard', 'Predictable results'],
                    'limitations': ['Limited to 4 colors', 'Less accurate color matching'],
                    'expected_channels': 4,
                    'quality': 'fair'
                }
            ]
        }

    def _score_all_methods(
        self,
        context: Dict,
        ai_recommendations: Dict
    ) -> List[MethodRecommendation]:
        """Score and rank all 6 methods"""

        methods = []

        # Primary recommendation from AI
        if 'recommended' in ai_recommendations:
            rec = ai_recommendations['recommended']
            methods.append(self._create_method_recommendation(rec, context))

        # Add alternatives
        for alt in ai_recommendations.get('alternatives', []):
            methods.append(self._create_method_recommendation(alt, context))

        # Sort by score
        methods.sort(key=lambda x: x.score, reverse=True)

        return methods

    def _create_method_recommendation(
        self,
        method_data: Dict,
        context: Dict
    ) -> MethodRecommendation:
        """Create MethodRecommendation from AI response data"""

        method_str = method_data.get('method', 'spot_color')

        # Validate method string
        try:
            method = SeparationMethod(method_str)
        except ValueError:
            print(f"  [AI] Invalid method '{method_str}', defaulting to spot_color")
            method = SeparationMethod.SPOT_COLOR

        return MethodRecommendation(
            method=method,
            method_name=method_data.get('method', 'spot_color').replace('_', ' ').title(),
            score=float(method_data.get('score', 50)),
            confidence=float(method_data.get('confidence', 0.5)),
            reasoning=method_data.get('reasoning', 'No reasoning provided'),
            strengths=method_data.get('strengths', []),
            limitations=method_data.get('limitations', []),
            best_for=self._get_best_for_text(method_str),
            expected_results={
                'channel_count': method_data.get('expected_channels', context['color_count']),
                'quality': method_data.get('quality', 'good'),
                'complexity': self._estimate_complexity(method_str),
                'cost': self._estimate_cost(method_data.get('expected_channels', 4))
            },
            palette_utilization={
                'colors_used': method_data.get('expected_channels', context['color_count']),
                'colors_total': context['color_count'],
                'percentage': (method_data.get('expected_channels', context['color_count']) /
                              max(context['color_count'], 1) * 100)
            }
        )

    def _get_best_for_text(self, method: str) -> str:
        """Get descriptive text for method use case"""
        descriptions = {
            'spot_color': 'Logos, graphics, text with solid colors',
            'simulated_process': 'Photographs, complex artwork, fine art prints',
            'index_color': 'Illustrations with moderate gradients',
            'cmyk': 'Standard commercial printing',
            'rgb': 'Experimental applications only',
            'hybrid_ai': 'Complex images with both vector and photo elements'
        }
        return descriptions.get(method, 'General use')

    def _estimate_complexity(self, method: str) -> str:
        """Estimate printing complexity"""
        complexity_map = {
            'spot_color': 'low',
            'index_color': 'moderate',
            'simulated_process': 'high',
            'cmyk': 'moderate',
            'rgb': 'low',
            'hybrid_ai': 'very_high'
        }
        return complexity_map.get(method, 'moderate')

    def _estimate_cost(self, channel_count: int) -> str:
        """Estimate printing cost"""
        if channel_count <= 4:
            return 'low'
        elif channel_count <= 8:
            return 'medium'
        else:
            return 'high'
