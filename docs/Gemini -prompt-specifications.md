# Gemini API Prompt Specification - Color Match Module
**Version:** 1.0  
**Date:** October 23, 2025  
**Purpose:** Define the prompt structure for AI-powered palette generation

---

## Overview

This specification defines how to structure prompts for Google Gemini AI to generate optimal screen printing color palettes based on image analysis data from the Analyze module.

---

## Input Data from Analyze Module

The Gemini prompt receives comprehensive analysis data:

### 1. Color Analysis Data
```python
{
    'total_unique_colors': int,              # e.g., 45000
    'color_complexity': {
        'complexity_score': float,            # 0-1 scale
        'color_variance': float,              # Color spread metric
        'range_L': float,                     # Lightness range 0-100
        'range_a': float,                     # Red-green range
        'range_b': float                      # Blue-yellow range
    },
    'gradient_analysis': {
        'gradient_present': bool,
        'mean_gradient': float,
        'max_gradient': float,
        'gradient_percentage': float          # % of image with gradients
    },
    'dominant_colors': [                      # Top 20 colors
        {
            'rgb': (int, int, int),
            'lab': (float, float, float),
            'pixel_count': int,
            'percentage': float,
            'variance': float
        }
    ],
    'kmeans_results': {                       # 8 different k-values
        'k4': {...}, 'k6': {...}, 'k8': {...},
        'k10': {...}, 'k12': {...}, 'k16': {...},
        'k20': {...}, 'k24': {...}
    }
}
```

### 2. Edge Analysis Data
```python
{
    'edge_type': str,                         # "sharp", "soft", "mixed"
    'line_work_score': float,                 # 0-1, higher = more vector-like
    'edge_density': float,                    # % of image that is edges
    'contour_count': int                      # Number of distinct contours
}
```

### 3. Texture Analysis Data
```python
{
    'texture_type': str,                      # "photo", "illustration", "halftone", "mixed"
    'texture_complexity': float,              # 0-1 scale
    'texture_uniformity': float,              # 0-1, higher = more uniform
    'halftone_analysis': {
        'halftone_detected': bool,
        'confidence': float,                  # 0-1
        'estimated_lpi': float,               # Lines per inch (if detected)
        'dominant_frequency': float
    }
}
```

---

## Prompt Structure

### Template Format

The prompt follows this structure:

```
[SYSTEM CONTEXT]
↓
[IMAGE ANALYSIS DATA]
↓
[USER REQUEST]
↓
[TASK INSTRUCTIONS]
↓
[OUTPUT FORMAT REQUIREMENTS]
↓
[CONSTRAINTS AND RULES]
```

---

## Full Prompt Template

```python
def build_gemini_prompt(
    color_analysis: dict,
    edge_analysis: dict,
    texture_analysis: dict,
    target_count: int,
    user_preferences: dict = None
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
    
    prompt = f"""
You are an expert screen printing color separation specialist with deep knowledge of:
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
- Total unique colors: {color_analysis['total_unique_colors']}
- Color complexity score: {color_analysis['color_complexity']['complexity_score']:.3f} (0-1 scale)
- Color variance: {color_analysis['color_complexity']['color_variance']:.2f}
- Color ranges:
  • L (lightness): {color_analysis['color_complexity']['range_L']:.1f}
  • a (red-green): {color_analysis['color_complexity']['range_a']:.1f}
  • b (blue-yellow): {color_analysis['color_complexity']['range_b']:.1f}

GRADIENTS:
- Gradient present: {color_analysis['gradient_analysis']['gradient_present']}
- Mean gradient: {color_analysis['gradient_analysis']['mean_gradient']:.2f}
- Max gradient: {color_analysis['gradient_analysis']['max_gradient']:.2f}
- Gradient coverage: {color_analysis['gradient_analysis']['gradient_percentage']:.1f}% of image

DOMINANT COLORS (Top 10):
{format_dominant_colors(color_analysis['dominant_colors'][:10])}

K-MEANS CLUSTERING RESULTS:
{format_kmeans_results(color_analysis['kmeans_results'])}

EDGE ANALYSIS:
- Edge type: {edge_analysis['edge_type']} (sharp/soft/mixed)
- Line work score: {edge_analysis['line_work_score']:.3f} (0-1, higher = more vector-like)
- Edge density: {edge_analysis['edge_density']:.2f}% of image
- Contour count: {edge_analysis['contour_count']} distinct contours

TEXTURE ANALYSIS:
- Texture type: {texture_analysis['texture_type']} (photo/illustration/halftone/mixed)
- Texture complexity: {texture_analysis['texture_complexity']:.3f} (0-1 scale)
- Texture uniformity: {texture_analysis['texture_uniformity']:.3f} (0-1, higher = more uniform)

HALFTONE DETECTION:
- Halftone detected: {texture_analysis['halftone_analysis']['halftone_detected']}
- Detection confidence: {texture_analysis['halftone_analysis']['confidence']:.3f}
{format_halftone_info(texture_analysis['halftone_analysis'])}

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
```

---

## Helper Functions for Formatting

```python
def format_dominant_colors(dominant_colors: list) -> str:
    """Format dominant colors for display in prompt"""
    lines = []
    for i, color in enumerate(dominant_colors, 1):
        rgb = color['rgb']
        lines.append(
            f"  {i}. RGB({rgb[0]}, {rgb[1]}, {rgb[2]}) - "
            f"{color['percentage']:.2f}% of image"
        )
    return "\n".join(lines)


def format_kmeans_results(kmeans_results: dict) -> str:
    """Format k-means clustering results"""
    lines = []
    for k_key in ['k4', 'k6', 'k8', 'k10', 'k12', 'k16', 'k20', 'k24']:
        if k_key in kmeans_results:
            result = kmeans_results[k_key]
            k_value = result['k']
            colors = result['colors_rgb']
            percentages = result['cluster_percentages']
            
            color_str = ", ".join([
                f"RGB({c[0]},{c[1]},{c[2]})={p:.1f}%"
                for c, p in zip(colors[:3], percentages[:3])
            ])
            
            lines.append(f"  k={k_value}: {color_str}...")
    
    return "\n".join(lines)


def format_halftone_info(halftone_analysis: dict) -> str:
    """Format halftone detection information"""
    if halftone_analysis['estimated_lpi']:
        return f"• Estimated LPI: {halftone_analysis['estimated_lpi']:.1f}\n" \
               f"• Dominant frequency: {halftone_analysis['dominant_frequency']:.4f}"
    else:
        return "• No LPI detected"


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
```

---

## Expected Response Format

Gemini will return JSON in this structure:

```json
{
  "overall_strategy": "Use 6-color spot separation with process yellow and magenta for skin tones, plus 4 custom spots for logo and background elements. Sharp edges suggest vector-style separation.",
  
  "palette": [
    {
      "name": "Background Blue",
      "rgb": [42, 87, 141],
      "pantone_match": "PMS 2945 C",
      "halftone_angle": 45,
      "suggested_frequency": 55,
      "coverage_estimate": 0.35,
      "layer_order": 1,
      "reasoning": "Dominant background color covering 35% of design. 45° angle provides optimal dot pattern."
    },
    {
      "name": "Skin Tone Base",
      "rgb": [234, 198, 175],
      "pantone_match": null,
      "halftone_angle": 15,
      "suggested_frequency": 65,
      "coverage_estimate": 0.18,
      "layer_order": 2,
      "reasoning": "Primary skin tone requiring higher LPI for smooth gradients. 15° angle separates from background."
    }
  ],
  
  "cmyk_alternative": {
    "feasible": true,
    "reasoning": "CMYK could reproduce this with 85% quality. Photographic elements would work well in process colors, but logo colors would be less accurate.",
    "estimated_quality_loss": 0.15
  },
  
  "production_notes": [
    "Print light to dark for optimal coverage",
    "Consider underbase white on dark garments",
    "Sharp edges detected - vector separation recommended"
  ],
  
  "confidence_score": 0.87
}
```

---

## API Configuration

### Gemini Model Settings

```python
GEMINI_CONFIG = {
    'model': 'gemini-1.5-pro',
    'temperature': 0.3,          # Lower = more consistent
    'top_p': 0.8,
    'top_k': 40,
    'max_output_tokens': 2048,
    'response_mime_type': 'application/json'
}
```

### Safety Settings

```python
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    }
]
```

---

## Error Handling

### Common Issues and Solutions

1. **Invalid JSON Response**
   - Parse error → Retry with clarified format requirements
   - Truncated response → Increase max_output_tokens

2. **Wrong Color Count**
   - Validate palette length matches target_count
   - If mismatch, extract reasoning from overall_strategy

3. **Missing Required Fields**
   - Validate all required fields present
   - Provide defaults where reasonable

4. **Invalid RGB Values**
   - Clamp to 0-255 range
   - Log warning for user review

---

## Testing Strategy

### Test Cases

1. **Simple Image** (2-3 colors)
   - Solid flat colors
   - Sharp edges
   - No gradients

2. **Complex Photographic** (8-12 colors)
   - Many colors
   - Soft gradients
   - High texture complexity

3. **Edge Cases**
   - Halftone detected (should note in response)
   - Extreme gradient (should recommend more colors)
   - Very high line work score (suggest vector separation)

### Validation Checklist

- [ ] JSON parses correctly
- [ ] Palette length matches target_count (or explains deviation)
- [ ] All RGB values in 0-255 range
- [ ] Halftone angles avoid moiré (30° minimum separation)
- [ ] LPI values reasonable (45-85 range)
- [ ] Layer order sequential 1-N
- [ ] Pantone matches valid or null
- [ ] Confidence score 0-1 range

---

## Integration Points

### Called By
- `ColorMatchCoordinator` → `GeminiPaletteGenerator.generate_palette()`

### Inputs From
- `AnalysisDataModel` (from Analyze module)
- User preferences (optional)

### Outputs To
- `PaletteManager` (stores generated palette)
- `ColorMatchDialog` (displays recommendation to user)

---

## Performance Considerations

1. **Prompt Length**: ~2000-3000 tokens (within Gemini limits)
2. **Response Time**: Typically 2-5 seconds
3. **Cost**: ~$0.002 per request (as of 2025 pricing)
4. **Caching**: Cache identical analysis+count combinations

---

## Future Enhancements

### Phase 2 Features
- [ ] Multi-image batch prompting
- [ ] Fine-tuned model for screen printing
- [ ] Image attachment support (when Gemini supports)
- [ ] Historical palette learning
- [ ] User feedback integration

---

## Summary

This Gemini prompt specification:

✅ Uses ALL analysis data from Analyze module  
✅ Provides comprehensive context for AI decision-making  
✅ Enforces structured JSON output  
✅ Includes screen printing domain expertise  
✅ Handles edge cases and validation  
✅ Integrates seamlessly with Color Match module  

The prompt is designed to produce professional-quality palette recommendations that balance artistic quality with print production constraints.

---

**End of Gemini Prompt Specification v1.0**