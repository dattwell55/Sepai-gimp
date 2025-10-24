"""
gemini_region_prompt.py - Prompt builder for AI Call #2 (Region Analysis)

Builds comprehensive prompts for Gemini to analyze image regions
and recommend optimal separation methods per region.
"""

import json
import re
from typing import List, Dict


class GeminiRegionAnalyzer:
    """
    Builds prompts and processes Gemini responses for region analysis
    """

    def build_region_analysis_prompt(
        self,
        image_characteristics: Dict,
        palette: List[Dict],
        preliminary_regions: List[Dict]
    ) -> str:
        """
        Build comprehensive prompt for Gemini region analysis

        Args:
            image_characteristics: From Analyze unit
            palette: Color palette from Color Match unit
            preliminary_regions: Initial segmentation from computer vision

        Returns:
            Formatted prompt string
        """

        prompt = f"""You are an expert screen printing color separation advisor. Analyze this image and recommend an intelligent region-based separation strategy.

IMAGE CONTEXT:
- Palette: {len(palette)} colors - {self._format_palette_summary(palette)}
- Overall Type: {image_characteristics.get('texture_type', 'mixed')}
- Has Gradients: {image_characteristics.get('has_gradients', 'unknown')}
- Edge Characteristics: {image_characteristics.get('edge_type', 'mixed')}

PRELIMINARY SEGMENTATION:
We've identified {len(preliminary_regions)} potential regions using computer vision:

{self._format_preliminary_regions(preliminary_regions)}

YOUR TASK:
Analyze this image and provide a region-based separation strategy. For each region, recommend the best separation method and explain your reasoning.

AVAILABLE SEPARATION METHODS:
1. **Spot Color** - Best for flat colors, sharp edges, vector-like content
   - Pros: Perfect color accuracy, crisp edges, low cost
   - Cons: Cannot handle gradients well

2. **Simulated Process** - Best for photographs, gradients, complex detail
   - Pros: Photorealistic quality, smooth gradients, fine detail
   - Cons: More complex printing, higher cost

3. **Index Color** - Best for moderate complexity, some gradients
   - Pros: Good balance of quality and cost
   - Cons: Some gradient banding possible

REGION ANALYSIS FRAMEWORK:
For each region, consider:

**Content Type:**
- Is this vector/graphic content or photographic?
- Are edges sharp or soft?
- Are colors flat or graduated?

**Color Characteristics:**
- How many distinct colors in this region?
- Are there smooth gradients?
- Is there texture or halftone patterns?

**Importance & Visibility:**
- Is this a primary focus area (logo, face) or background?
- Does this region require highest fidelity?

**Method Selection Logic:**
- Vector-like regions -> Spot Color
- Photo-like regions -> Simulated Process
- Mixed regions -> Index Color or evaluate hybrid sub-approach

RESPONSE FORMAT (JSON):
{{
  "overall_strategy": "Brief summary of your approach (2-3 sentences)",
  "complexity_rating": "simple|moderate|complex",
  "regions": [
    {{
      "region_id": "region_1",
      "content_description": "What is in this region (e.g., 'logo text', 'portrait background')",
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
    }}
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

IMPORTANT GUIDELINES:
- Be specific about WHY you chose each method
- Consider how regions interact (overlaps, transitions)
- Balance quality with printing complexity
- Flag any uncertainty in your recommendations
- Think about the final printed result on fabric/paper

Now analyze this image and provide your expert region-based separation strategy:
"""

        return prompt

    def _format_palette_summary(self, palette: List[Dict]) -> str:
        """Format palette for prompt"""
        if len(palette) <= 3:
            return ", ".join([f"{c['name']} ({c['hex']})" for c in palette])
        else:
            first_three = ", ".join([f"{c['name']}" for c in palette[:3]])
            return f"{first_three}, and {len(palette)-3} more colors"

    def _format_preliminary_regions(self, regions: List[Dict]) -> str:
        """Format preliminary segmentation results"""
        lines = []
        for i, region in enumerate(regions, 1):
            lines.append(
                f"Region {i}: {region['type']} area, "
                f"{region['coverage']:.1f}% of image, "
                f"edge sharpness {region['edge_sharpness']:.2f}"
            )
        return "\n".join(lines)

    def parse_gemini_response(self, response_text: str) -> Dict:
        """
        Parse Gemini's JSON response into structured data

        Args:
            response_text: Raw Gemini response

        Returns:
            Parsed region analysis dictionary
        """
        # Extract JSON from response (may be wrapped in markdown)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in Gemini response")

        try:
            data = json.loads(json_match.group())

            # Validate required fields
            required_fields = ['overall_strategy', 'regions', 'expected_results']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Gemini response: {e}")
