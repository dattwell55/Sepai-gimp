#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API Prompt Builder for Palette Generation
Builds comprehensive prompts for AI-powered color palette generation
"""

from typing import Dict, Optional, List
import json


def build_gemini_prompt(
    color_analysis: dict,
    edge_analysis: dict,
    texture_analysis: dict,
    target_count: int,
    user_preferences: Optional[dict] = None
) -> str:
    """
    Build the complete Gemini prompt for palette generation

    Args:
        color_analysis: Color analysis results from Analyze module
        edge_analysis: Edge analysis results from Analyze module
        texture_analysis: Texture analysis results from Analyze module
        target_count: Desired number of colors (2-24)
        user_preferences: Optional user preferences/constraints

    Returns:
        Complete formatted prompt string
    """

    prompt = f"""You are an expert screen printing color separation specialist with deep knowledge of:
- Spot color separation techniques
- Halftone angles and screen frequencies
- Pantone color matching
- Print production workflows
- Color mixing and ink formulation

Analyze this image and provide a comprehensive palette recommendation.

═══════════════════════════════════════════════════════════════════
IMAGE ANALYSIS DATA (from automated analysis):
═══════════════════════════════════════════════════════════════════

COLOR ANALYSIS:
- Total unique colors: {color_analysis.get('unique_color_count', 'N/A')}
- Color complexity score: {color_analysis.get('color_complexity', 0.5):.3f} (0-1 scale)
- Dominant color clusters: {len(color_analysis.get('clusters', []))}
- Has gradients: {color_analysis.get('has_gradients', False)}
- Has fine details: {color_analysis.get('has_fine_details', False)}
- Recommended method: {color_analysis.get('recommended_method', 'spot_color')}

DOMINANT COLORS (Top 10):
{format_dominant_colors(color_analysis.get('clusters', [])[:10])}

EDGE ANALYSIS:
- Edge type: {_classify_edge_type(edge_analysis)}
- Edge density: {edge_analysis.get('edge_density', 0.0):.2f}% of image
- Edge sharpness: {edge_analysis.get('edge_sharpness', 0.5):.3f} (0-1 scale)
- Detail level: {edge_analysis.get('detail_level', 'medium')}
- Has fine lines: {edge_analysis.get('has_fine_lines', False)}
- Contour count: {edge_analysis.get('contour_count', 0)} distinct contours

TEXTURE ANALYSIS:
- Texture type: {_classify_texture_type(texture_analysis)}
- Texture complexity: {texture_analysis.get('texture_complexity', 0.5):.3f} (0-1 scale)
- Grain size: {texture_analysis.get('grain_size', 'none')}
- Noise level: {texture_analysis.get('noise_level', 0.0):.3f}
- Has screens/halftones: {texture_analysis.get('has_screens', False)}
- Dominant patterns: {', '.join(texture_analysis.get('dominant_patterns', [])) or 'None'}

═══════════════════════════════════════════════════════════════════
USER REQUEST:
═══════════════════════════════════════════════════════════════════
Target palette size: {target_count} colors

{format_user_preferences(user_preferences) if user_preferences else ''}

═══════════════════════════════════════════════════════════════════
YOUR TASK:
═══════════════════════════════════════════════════════════════════

Based on the image and analysis data, provide a comprehensive palette recommendation.

**Consider these factors in your decision:**

1. **Color Count Optimization**
   - Balance quality vs. cost (fewer colors = cheaper printing)
   - Determine if the requested color count is optimal
   - Suggest alternatives if necessary

2. **Separation Strategy**
   - Spot colors for solid areas
   - Process colors (CMYK) for photographic elements
   - Hybrid approach when appropriate
   - Special considerations for gradients

3. **Halftone Configuration**
   - Optimal screen angles to avoid moiré patterns
   - Appropriate line frequencies (LPI) for each color
   - Consider substrate and printing method

4. **Color Matching**
   - Identify closest Pantone equivalents where applicable
   - Consider ink mixing vs. spot colors
   - Account for substrate (assume white paper unless specified)

5. **Print Production**
   - Registration concerns
   - Trapping requirements
   - Ink opacity and layering order

═══════════════════════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT (respond with valid JSON only):
═══════════════════════════════════════════════════════════════════

{{
  "overall_strategy": "Brief 1-2 sentence explanation of your approach",

  "palette": [
    {{
      "name": "Descriptive color name",
      "rgb": [R, G, B],
      "pantone_match": "PMS XXXX C" or null,
      "halftone_angle": 45,
      "suggested_frequency": 55,
      "coverage_estimate": 0.XX,
      "layer_order": 1,
      "reasoning": "Why this color and these settings"
    }}
  ],

  "cmyk_alternative": {{
    "feasible": true/false,
    "reasoning": "Why CMYK would or wouldn't work",
    "estimated_quality_loss": 0.XX
  }},

  "production_notes": [
    "Important note 1",
    "Important note 2"
  ],

  "confidence_score": 0.XX
}}

═══════════════════════════════════════════════════════════════════
CONSTRAINTS AND RULES:
═══════════════════════════════════════════════════════════════════

1. **Color Count**: Generate exactly {target_count} colors (unless you strongly recommend otherwise, then explain in overall_strategy)

2. **Halftone Angles**: Use standard angles to avoid moiré:
   - 45° (most common, visually pleasing)
   - 15°, 75° (secondary angles)
   - 0°, 90° (for special cases)
   - Minimum 30° separation between colors

3. **Screen Frequency**: Typical range 45-85 LPI
   - 45-55 LPI: Coarse/bold prints, textiles
   - 55-65 LPI: Standard screen printing
   - 65-85 LPI: Fine detail work

4. **Layer Order**: 1 = first layer (usually lightest), N = last (usually darkest)

5. **Coverage Estimate**: 0.0-1.0 scale representing approximate % of design

6. **Pantone Matching**: Only suggest if close match exists (ΔE < 5)

7. **RGB Values**: Must be valid 0-255 integers

8. **Response**: MUST be valid JSON only, no additional text before or after

═══════════════════════════════════════════════════════════════════
BEGIN YOUR ANALYSIS:
═══════════════════════════════════════════════════════════════════
"""

    return prompt


def format_dominant_colors(clusters: List[dict]) -> str:
    """Format dominant colors for display in prompt"""
    if not clusters:
        return "  (No cluster data available)"

    lines = []
    for i, cluster in enumerate(clusters, 1):
        rgb = cluster.get('center_rgb', (0, 0, 0))
        percentage = cluster.get('percentage', 0.0)

        lines.append(
            f"  {i}. RGB({rgb[0]}, {rgb[1]}, {rgb[2]}) - "
            f"{percentage:.2f}% of image"
        )

    return "\n".join(lines) if lines else "  (No colors identified)"


def format_user_preferences(preferences: dict) -> str:
    """Format optional user preferences"""
    lines = ["User Preferences:"]

    if 'max_colors' in preferences:
        lines.append(f"- Maximum colors: {preferences['max_colors']}")
    if 'avoid_cmyk' in preferences:
        lines.append(f"- Avoid CMYK: {preferences['avoid_cmyk']}")
    if 'prefer_pantone' in preferences:
        lines.append(f"- Prefer Pantone: {preferences['prefer_pantone']}")
    if 'substrate' in preferences:
        lines.append(f"- Substrate: {preferences['substrate']}")
    if 'notes' in preferences:
        lines.append(f"- Additional notes: {preferences['notes']}")

    return "\n".join(lines)


def _classify_edge_type(edge_analysis: dict) -> str:
    """Classify edge type from analysis data"""
    sharpness = edge_analysis.get('edge_sharpness', 0.5)

    if sharpness > 0.7:
        return "sharp"
    elif sharpness < 0.3:
        return "soft"
    else:
        return "mixed"


def _classify_texture_type(texture_analysis: dict) -> str:
    """Classify texture type from analysis data"""
    patterns = texture_analysis.get('dominant_patterns', [])
    has_screens = texture_analysis.get('has_screens', False)
    complexity = texture_analysis.get('texture_complexity', 0.5)

    if has_screens or 'halftone' in patterns:
        return "halftone"
    elif complexity > 0.7:
        return "photo"
    elif complexity < 0.3:
        return "illustration"
    else:
        return "mixed"


def parse_gemini_response(response_text: str) -> Optional[Dict]:
    """
    Parse Gemini's JSON response

    Args:
        response_text: Raw text response from Gemini

    Returns:
        Parsed palette data or None if parsing failed
    """
    try:
        # Try to find JSON in response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)

            # Validate required fields
            if 'palette' in data and isinstance(data['palette'], list):
                return data

    except Exception as e:
        print(f"Error parsing Gemini response: {e}")

    return None


def validate_palette(palette_data: dict, target_count: int) -> List[str]:
    """
    Validate palette data from Gemini

    Args:
        palette_data: Parsed Gemini response
        target_count: Expected number of colors

    Returns:
        List of validation warnings (empty if all valid)
    """
    warnings = []

    # Check palette length
    palette = palette_data.get('palette', [])
    if len(palette) != target_count:
        warnings.append(
            f"Expected {target_count} colors, got {len(palette)}"
        )

    # Validate each color
    for i, color in enumerate(palette):
        # Check RGB values
        rgb = color.get('rgb', [])
        if len(rgb) != 3:
            warnings.append(f"Color {i+1}: Invalid RGB format")
        else:
            for channel in rgb:
                if not (0 <= channel <= 255):
                    warnings.append(f"Color {i+1}: RGB value out of range")

        # Check halftone angle
        angle = color.get('halftone_angle')
        if angle is not None and not (0 <= angle <= 90):
            warnings.append(f"Color {i+1}: Invalid halftone angle {angle}")

        # Check LPI
        lpi = color.get('suggested_frequency')
        if lpi is not None and not (30 <= lpi <= 120):
            warnings.append(f"Color {i+1}: Unusual LPI value {lpi}")

    # Check for moiré (angle separation)
    angles = [c.get('halftone_angle', 45) for c in palette]
    for i in range(len(angles)):
        for j in range(i + 1, len(angles)):
            diff = abs(angles[i] - angles[j])
            if diff < 30 and diff != 0:
                warnings.append(
                    f"Potential moiré: Colors {i+1} and {j+1} "
                    f"have only {diff}° angle separation"
                )

    return warnings


# Gemini API configuration constants
GEMINI_CONFIG = {
    'model': 'gemini-1.5-pro',
    'temperature': 0.3,          # Lower = more consistent
    'top_p': 0.8,
    'top_k': 40,
    'max_output_tokens': 2048,
}
