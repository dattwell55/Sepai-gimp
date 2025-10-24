#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Method Recommendation Prompt Builder - AI Call #1
Builds prompts for Gemini to recommend optimal separation methods
"""

from typing import Dict, List, Optional
import json


def build_method_recommendation_prompt(
    analysis_data: Dict,
    palette_data: Dict,
    user_preferences: Optional[Dict] = None
) -> str:
    """
    Build comprehensive prompt for method recommendation (AI Call #1)

    Args:
        analysis_data: Image analysis results
        palette_data: Color palette data
        user_preferences: Optional user constraints

    Returns:
        Formatted prompt string for Gemini
    """

    # Extract key characteristics
    color_count = len(palette_data.get('palette', []))
    palette_colors = palette_data.get('palette', [])

    # Get analysis characteristics
    color_analysis = analysis_data.get('color_analysis', {})
    edge_analysis = analysis_data.get('edge_analysis', {})
    texture_analysis = analysis_data.get('texture_analysis', {})

    # Build palette summary
    palette_summary = _format_palette_for_prompt(palette_colors[:5])

    prompt = f"""You are an expert screen printing color separation advisor with deep knowledge of:
- Spot color separation techniques
- Simulated process/CMYK separation
- Index color quantization
- Halftone screening and moiré patterns
- Print production workflows
- Cost vs. quality tradeoffs

═══════════════════════════════════════════════════════════════════
IMAGE & PALETTE ANALYSIS:
═══════════════════════════════════════════════════════════════════

PALETTE:
- Total Colors: {color_count}
- Top Colors:
{palette_summary}

COLOR CHARACTERISTICS:
- Unique Color Count: {color_analysis.get('unique_color_count', 'N/A')}
- Color Complexity: {color_analysis.get('color_complexity', 0.0):.3f} (0-1 scale)
- Has Gradients: {color_analysis.get('has_gradients', False)}
- Gradient Quality: {'Smooth' if color_analysis.get('color_complexity', 0) > 0.6 else 'Limited'}

EDGE & DETAIL:
- Edge Density: {edge_analysis.get('edge_density', 0.0):.2f}
- Edge Sharpness: {edge_analysis.get('edge_sharpness', 0.5):.3f} (0-1 scale)
- Detail Level: {edge_analysis.get('detail_level', 'medium')}
- Has Fine Lines: {edge_analysis.get('has_fine_lines', False)}
- Has Halftones: {edge_analysis.get('has_halftones', False)}

TEXTURE:
- Texture Type: {_classify_texture(texture_analysis)}
- Complexity: {texture_analysis.get('texture_complexity', 0.5):.3f} (0-1 scale)
- Grain Size: {texture_analysis.get('grain_size', 'none')}
- Has Screens: {texture_analysis.get('has_screens', False)}

{_format_user_constraints(user_preferences) if user_preferences else ''}

═══════════════════════════════════════════════════════════════════
AVAILABLE SEPARATION METHODS:
═══════════════════════════════════════════════════════════════════

1. **SPOT COLOR** (spot_color)
   - Best for: 2-8 solid colors, logos, graphics, vector art
   - Strengths: Perfect color matching, crisp edges, lowest cost
   - Limitations: Cannot handle gradients well, limited to flat colors
   - Typical use: T-shirts, simple designs, brand logos

2. **SIMULATED PROCESS** (simulated_process)
   - Best for: Photographs, complex gradients, realistic images
   - Strengths: Photorealistic quality, smooth gradients, fine detail
   - Limitations: Higher printing cost, requires skilled printer
   - Typical use: Photo prints, detailed artwork, portraits

3. **INDEX COLOR** (index_color)
   - Best for: 6-12 colors, mixed content, moderate complexity
   - Strengths: Good balance of quality and cost, handles some gradients
   - Limitations: Some gradient banding, not as precise as spot color
   - Typical use: Posters, vintage designs, moderate complexity artwork

4. **CMYK** (cmyk)
   - Best for: Standard 4-color process, print shops with CMYK setup
   - Strengths: Industry standard, widely supported, good for photos
   - Limitations: Limited color gamut, may not match spot colors exactly
   - Typical use: Commercial printing, magazines, standard process work

5. **HYBRID AI** (hybrid_ai) - ADVANCED
   - Best for: Complex images with mixed content (logo + photo, graphics + texture)
   - Strengths: Intelligent region-based separation, best quality
   - Limitations: Longest processing time, requires AI Call #2, most complex
   - Typical use: High-end work, limited editions, museum prints

6. **RGB** (rgb)
   - Best for: Specialty inks, unique substrates, experimental work
   - Strengths: Different color space, special effects
   - Limitations: Rarely used in traditional screen printing
   - Typical use: Specialty applications only

═══════════════════════════════════════════════════════════════════
YOUR TASK:
═══════════════════════════════════════════════════════════════════

Analyze the image characteristics and palette, then recommend:

1. **PRIMARY METHOD** - The best separation approach for this image
2. **ALTERNATIVE #1** - Second-best option if user wants different tradeoff
3. **ALTERNATIVE #2** - Third option for comparison

For EACH method recommendation, provide:
- Method name (use exact values: spot_color, simulated_process, index_color, cmyk, hybrid_ai, rgb)
- Score (0-100) based on how well it fits this image
- Confidence (0.0-1.0) in this recommendation
- Detailed reasoning (3-5 sentences explaining WHY this method is ideal)
- Key strengths (3-5 specific benefits for THIS image)
- Limitations (2-4 specific drawbacks or concerns)
- Expected channel count
- Quality rating (excellent, good, fair, poor)
- Estimated print complexity (low, moderate, high, very_high)
- Estimated cost level (low, moderate, high, very_high)

═══════════════════════════════════════════════════════════════════
DECISION CRITERIA:
═══════════════════════════════════════════════════════════════════

**Spot Color** when:
✓ Edge sharpness > 0.7
✓ No gradients or minimal gradients
✓ 2-8 distinct colors
✓ Low texture complexity
✓ High line work score

**Simulated Process** when:
✓ Has smooth gradients
✓ Photo-like texture
✓ 4-12 colors
✓ Medium-high complexity
✓ Soft edges

**Index Color** when:
✓ 6-12 colors
✓ Mixed characteristics
✓ Moderate complexity
✓ Some gradients acceptable
✓ Balance of cost and quality needed

**CMYK** when:
✓ Standard process preferred
✓ Photo content
✓ Industry compatibility important

**Hybrid AI** when:
✓ Mixed content (vector + photo)
✓ Different regions need different methods
✓ Quality is top priority
✓ Budget allows for complexity

**RGB** - Rarely recommend unless:
✓ Special request
✓ Specialty inks
✓ Experimental work

═══════════════════════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT (JSON only):
═══════════════════════════════════════════════════════════════════

{{
  "recommended": {{
    "method": "spot_color",
    "method_name": "Spot Color Separation",
    "score": 95,
    "confidence": 0.95,
    "reasoning": "Detailed explanation of why this is the best choice...",
    "strengths": [
      "Strength 1 specific to this image",
      "Strength 2",
      "Strength 3",
      "Strength 4"
    ],
    "limitations": [
      "Limitation 1",
      "Limitation 2"
    ],
    "expected_channels": 4,
    "quality_rating": "excellent",
    "print_complexity": "low",
    "cost_level": "low",
    "best_for": "Brief description of when to use this"
  }},

  "alternative_1": {{
    "method": "index_color",
    "method_name": "Index Color Separation",
    "score": 78,
    "confidence": 0.80,
    "reasoning": "...",
    "strengths": ["...", "..."],
    "limitations": ["..."],
    "expected_channels": 6,
    "quality_rating": "good",
    "print_complexity": "moderate",
    "cost_level": "moderate",
    "best_for": "..."
  }},

  "alternative_2": {{
    "method": "cmyk",
    "method_name": "CMYK Process",
    "score": 65,
    "confidence": 0.70,
    "reasoning": "...",
    "strengths": ["...", "..."],
    "limitations": ["..."],
    "expected_channels": 4,
    "quality_rating": "good",
    "print_complexity": "moderate",
    "cost_level": "moderate",
    "best_for": "..."
  }},

  "overall_assessment": {{
    "image_type": "vector|photo|mixed|illustration",
    "complexity_rating": "simple|moderate|complex",
    "primary_challenge": "Brief description of main separation challenge",
    "recommended_approach": "High-level strategy summary"
  }}
}}

IMPORTANT:
- Respond with VALID JSON ONLY
- Use exact method names from the list
- Be specific about strengths/limitations FOR THIS IMAGE
- Consider cost vs. quality tradeoffs
- Think about the final printed result

═══════════════════════════════════════════════════════════════════
BEGIN YOUR ANALYSIS:
═══════════════════════════════════════════════════════════════════
"""

    return prompt


def _format_palette_for_prompt(colors: List[Dict]) -> str:
    """Format palette colors for display in prompt"""
    if not colors:
        return "  (No colors provided)"

    lines = []
    for i, color in enumerate(colors, 1):
        rgb = color.get('rgb', [0, 0, 0])
        name = color.get('name', f'Color {i}')
        pantone = color.get('pantone_match', 'None')
        coverage = color.get('coverage_estimate', 0.0)

        lines.append(
            f"  {i}. {name}: RGB({rgb[0]}, {rgb[1]}, {rgb[2]}) "
            f"| Pantone: {pantone} | Coverage: {coverage*100:.1f}%"
        )

    return "\n".join(lines)


def _classify_texture(texture_analysis: Dict) -> str:
    """Classify texture type from analysis"""
    patterns = texture_analysis.get('dominant_patterns', [])
    complexity = texture_analysis.get('texture_complexity', 0.5)

    if 'halftone' in patterns or texture_analysis.get('has_screens'):
        return "Halftone/Screened"
    elif complexity > 0.7:
        return "Photographic"
    elif complexity < 0.3:
        return "Flat/Vector"
    else:
        return "Mixed/Moderate"


def _format_user_constraints(preferences: Dict) -> str:
    """Format user preferences/constraints"""
    lines = ["USER PREFERENCES:"]

    if 'max_colors' in preferences:
        lines.append(f"- Maximum colors: {preferences['max_colors']}")
    if 'prefer_quality' in preferences:
        lines.append(f"- Quality priority: {'High' if preferences['prefer_quality'] else 'Standard'}")
    if 'budget_conscious' in preferences:
        lines.append(f"- Budget conscious: {preferences['budget_conscious']}")
    if 'print_method' in preferences:
        lines.append(f"- Print method: {preferences['print_method']}")
    if 'notes' in preferences:
        lines.append(f"- Notes: {preferences['notes']}")

    return "\n".join(lines) + "\n"


def parse_method_recommendation_response(response_text: str) -> Optional[Dict]:
    """
    Parse Gemini's method recommendation response

    Args:
        response_text: Raw response from Gemini

    Returns:
        Parsed recommendation data or None
    """
    try:
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)

            # Validate structure
            if 'recommended' in data and 'method' in data['recommended']:
                return data

    except Exception as e:
        print(f"Error parsing method recommendation: {e}")

    return None


def validate_method_recommendation(recommendation: Dict) -> List[str]:
    """
    Validate recommendation data

    Returns:
        List of validation warnings (empty if valid)
    """
    warnings = []

    valid_methods = [
        'spot_color', 'simulated_process', 'index_color',
        'cmyk', 'hybrid_ai', 'rgb'
    ]

    # Check recommended method
    if 'recommended' in recommendation:
        method = recommendation['recommended'].get('method')
        if method not in valid_methods:
            warnings.append(f"Invalid method: {method}")

        score = recommendation['recommended'].get('score', 0)
        if not (0 <= score <= 100):
            warnings.append(f"Invalid score: {score}")

        confidence = recommendation['recommended'].get('confidence', 0)
        if not (0 <= confidence <= 1):
            warnings.append(f"Invalid confidence: {confidence}")
    else:
        warnings.append("Missing 'recommended' field")

    return warnings


# Configuration for Gemini API
METHOD_RECOMMENDATION_CONFIG = {
    'model': 'gemini-1.5-pro',
    'temperature': 0.2,        # Lower for more consistent recommendations
    'top_p': 0.8,
    'top_k': 40,
    'max_output_tokens': 2048,
}
