#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Region Analysis Prompt Builder - AI Call #2 (Hybrid AI Separation)
Builds prompts for Gemini to analyze image regions and recommend per-region methods
"""

from typing import Dict, List, Optional
import json


def build_region_analysis_prompt(
    preliminary_regions: List[Dict],
    palette_data: Dict,
    analysis_data: Dict
) -> str:
    """
    Build comprehensive prompt for region analysis (AI Call #2 - Hybrid only)

    Args:
        preliminary_regions: Initial computer vision segmentation results
        palette_data: Color palette from Color Match
        analysis_data: Image analysis from Analyze unit

    Returns:
        Formatted prompt string for Gemini with image
    """

    color_count = len(palette_data.get('palette', []))
    palette_colors = palette_data.get('palette', [])

    # Get overall characteristics
    color_analysis = analysis_data.get('color_analysis', {})
    edge_analysis = analysis_data.get('edge_analysis', {})
    texture_analysis = analysis_data.get('texture_analysis', {})

    prompt = f"""You are an expert screen printing color separation advisor. Analyze this image and recommend an intelligent region-based separation strategy.

═══════════════════════════════════════════════════════════════════
IMAGE CONTEXT:
═══════════════════════════════════════════════════════════════════

PALETTE:
- Total Colors: {color_count}
- {_format_palette_summary(palette_colors)}

OVERALL IMAGE CHARACTERISTICS:
- Type: {_classify_overall_type(texture_analysis, edge_analysis)}
- Has Gradients: {color_analysis.get('has_gradients', 'unknown')}
- Edge Type: {_classify_edge_type(edge_analysis)}
- Complexity: {color_analysis.get('color_complexity', 0.5):.2f} (0-1 scale)

═══════════════════════════════════════════════════════════════════
PRELIMINARY SEGMENTATION:
═══════════════════════════════════════════════════════════════════

We've identified {len(preliminary_regions)} potential regions using computer vision:

{_format_preliminary_regions(preliminary_regions)}

═══════════════════════════════════════════════════════════════════
YOUR TASK:
═══════════════════════════════════════════════════════════════════

Analyze this image and provide a region-based separation strategy. For each region, recommend the best separation method and explain your reasoning.

AVAILABLE SEPARATION METHODS:

1. **Spot Color** (spot_color)
   - Best for: Flat colors, sharp edges, vector-like content, logos, text
   - Pros: Perfect color accuracy, crisp edges, low cost
   - Cons: Cannot handle gradients well

2. **Simulated Process** (simulated_process)
   - Best for: Photographs, gradients, complex detail, portraits
   - Pros: Photorealistic quality, smooth gradients, fine detail
   - Cons: More complex printing, higher cost

3. **Index Color** (index_color)
   - Best for: Moderate complexity, some gradients, mixed content
   - Pros: Good balance of quality and cost
   - Cons: Some gradient banding possible

═══════════════════════════════════════════════════════════════════
REGION ANALYSIS FRAMEWORK:
═══════════════════════════════════════════════════════════════════

For EACH region, consider:

**Content Type:**
- Is this vector/graphic content or photographic?
- Are edges sharp or soft?
- Are colors flat or graduated?
- Is there text or linework?

**Color Characteristics:**
- How many distinct colors in this region?
- Are there smooth gradients?
- Is there texture or halftone patterns?
- Color complexity within region?

**Importance & Visibility:**
- Is this a primary focus area (logo, face, main subject) or background?
- Does this region require highest fidelity?
- How prominent is this region in the overall design?

**Method Selection Logic:**
- Vector-like regions (sharp, flat) → Spot Color
- Photo-like regions (soft, gradients) → Simulated Process
- Mixed regions (some gradients, moderate detail) → Index Color

═══════════════════════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT (respond with valid JSON only):
═══════════════════════════════════════════════════════════════════

{{
  "overall_strategy": "Brief 2-3 sentence explanation of your region-based approach",

  "complexity_rating": "simple|moderate|complex",

  "regions": [
    {{
      "region_id": "region_1",
      "content_description": "What is in this region (e.g., 'logo text', 'portrait background', 'product photo')",
      "region_type": "vector|photo|text|mixed|background",
      "complexity": "simple|moderate|complex",

      "characteristics": {{
        "dominant_colors": ["#FF0000", "#0000FF"],
        "has_gradients": true|false,
        "edge_sharpness": 0.0-1.0,
        "texture_present": true|false
      }},

      "recommended_method": "spot_color|simulated_process|index_color",
      "method_confidence": 0.0-1.0,
      "reasoning": "Why this method is best for this region (2-3 sentences)",

      "priority": 1-10,
      "alternatives": [
        {{
          "method": "alternative_method",
          "confidence": 0.0-1.0,
          "note": "When to consider this alternative"
        }}
      ]
    }},
    ... more regions ...
  ],

  "region_interactions": [
    {{
      "region_pair": ["region_1", "region_2"],
      "relationship": "adjacent|overlapping|separate",
      "blending_needed": true|false,
      "transition_complexity": "simple|moderate|complex"
    }}
  ],

  "expected_results": {{
    "quality_rating": "excellent|good|fair",
    "channel_count": 4-12,
    "print_complexity": "low|moderate|high|very_high"
  }},

  "confidence_assessment": {{
    "overall_confidence": 0.0-1.0,
    "uncertainty_areas": ["List any regions where method choice is ambiguous"],
    "improvement_suggestions": ["Optional user adjustments that could improve results"]
  }}
}}

═══════════════════════════════════════════════════════════════════
IMPORTANT GUIDELINES:
═══════════════════════════════════════════════════════════════════

✓ Be specific about WHY you chose each method for each region
✓ Consider how regions interact (overlaps, transitions, boundaries)
✓ Balance quality with printing complexity and cost
✓ Flag any uncertainty in your recommendations
✓ Think about the final printed result on fabric/paper
✓ Provide actionable reasoning that helps users understand decisions
✓ Consider registration concerns between regions
✓ Think about ink opacity and layering order

RESPOND WITH VALID JSON ONLY - no markdown, no explanation before or after.

═══════════════════════════════════════════════════════════════════
NOW ANALYZE THIS IMAGE:
═══════════════════════════════════════════════════════════════════
"""

    return prompt


def _format_palette_summary(palette: List[Dict]) -> str:
    """Format palette for prompt summary"""
    if not palette:
        return "(No colors)"

    if len(palette) <= 3:
        return ", ".join([f"{c.get('name', 'Color')} ({_rgb_to_hex(c.get('rgb', [0,0,0]))})" for c in palette])
    else:
        first_three = ", ".join([f"{c.get('name', 'Color')}" for c in palette[:3]])
        return f"{first_three}, and {len(palette)-3} more"


def _rgb_to_hex(rgb: List[int]) -> str:
    """Convert RGB list to hex string"""
    if len(rgb) != 3:
        return "#000000"
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _classify_overall_type(texture_analysis: Dict, edge_analysis: Dict) -> str:
    """Classify overall image type"""
    texture_type = texture_analysis.get('dominant_patterns', [])
    edge_sharp = edge_analysis.get('edge_sharpness', 0.5)

    if edge_sharp > 0.7 and 'textured' not in texture_type:
        return "Vector/Graphic"
    elif 'halftone' in texture_type or texture_analysis.get('has_screens'):
        return "Halftone/Photo"
    elif texture_analysis.get('texture_complexity', 0) > 0.6:
        return "Photographic"
    else:
        return "Mixed"


def _classify_edge_type(edge_analysis: Dict) -> str:
    """Classify edge type"""
    sharpness = edge_analysis.get('edge_sharpness', 0.5)

    if sharpness > 0.7:
        return "Sharp/Vector"
    elif sharpness < 0.3:
        return "Soft/Photo"
    else:
        return "Mixed"


def _format_preliminary_regions(regions: List[Dict]) -> str:
    """Format preliminary segmentation results"""
    if not regions:
        return "(No regions detected)"

    lines = []
    for i, region in enumerate(regions, 1):
        region_type = region.get('type', 'unknown')
        coverage = region.get('coverage', 0.0)
        edge_sharp = region.get('edge_sharpness', 0.5)
        has_grad = region.get('has_gradients', False)

        lines.append(
            f"Region {i}: {region_type} area | "
            f"{coverage:.1f}% of image | "
            f"Edge sharpness {edge_sharp:.2f} | "
            f"Gradients: {'Yes' if has_grad else 'No'}"
        )

    return "\n".join(lines)


def parse_region_analysis_response(response_text: str) -> Optional[Dict]:
    """
    Parse Gemini's region analysis response

    Args:
        response_text: Raw text response from Gemini

    Returns:
        Parsed region analysis data or None if parsing failed
    """
    try:
        # Try to find JSON in response (may be wrapped in markdown)
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

        if not json_match:
            print("No JSON found in Gemini response")
            return None

        json_str = json_match.group()
        data = json.loads(json_str)

        # Validate required fields
        required_fields = ['overall_strategy', 'regions', 'expected_results']
        for field in required_fields:
            if field not in data:
                print(f"Missing required field: {field}")
                return None

        return data

    except json.JSONDecodeError as e:
        print(f"Invalid JSON in Gemini response: {e}")
        return None
    except Exception as e:
        print(f"Error parsing region analysis: {e}")
        return None


def validate_region_analysis(region_data: Dict, expected_region_count: int) -> List[str]:
    """
    Validate region analysis data from Gemini

    Args:
        region_data: Parsed Gemini response
        expected_region_count: Expected number of regions

    Returns:
        List of validation warnings (empty if all valid)
    """
    warnings = []

    # Check region count
    regions = region_data.get('regions', [])
    if len(regions) != expected_region_count:
        warnings.append(
            f"Expected {expected_region_count} regions, got {len(regions)}"
        )

    # Validate each region
    valid_methods = ['spot_color', 'simulated_process', 'index_color']
    valid_types = ['vector', 'photo', 'text', 'mixed', 'background']

    for i, region in enumerate(regions):
        # Check method
        method = region.get('recommended_method')
        if method not in valid_methods:
            warnings.append(f"Region {i+1}: Invalid method '{method}'")

        # Check region type
        reg_type = region.get('region_type')
        if reg_type not in valid_types:
            warnings.append(f"Region {i+1}: Invalid type '{reg_type}'")

        # Check confidence
        confidence = region.get('method_confidence', 0)
        if not (0 <= confidence <= 1):
            warnings.append(f"Region {i+1}: Invalid confidence {confidence}")

        # Check priority
        priority = region.get('priority', 5)
        if not (1 <= priority <= 10):
            warnings.append(f"Region {i+1}: Invalid priority {priority}")

    # Check overall confidence
    overall_conf = region_data.get('confidence_assessment', {}).get('overall_confidence', 0)
    if not (0 <= overall_conf <= 1):
        warnings.append(f"Invalid overall confidence: {overall_conf}")

    return warnings


# Configuration for Gemini API (AI Call #2)
REGION_ANALYSIS_CONFIG = {
    'model': 'gemini-1.5-pro',   # Needs vision capabilities
    'temperature': 0.3,           # Slightly higher for more nuanced analysis
    'top_p': 0.8,
    'top_k': 40,
    'max_output_tokens': 3072,   # Larger for multiple regions
}
