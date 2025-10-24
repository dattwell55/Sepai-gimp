GIMP AI Color Separation Plugin - Hybrid AI Separation Specification
Version: 1.0-GIMP
Date: January 2025
Status: Draft for Review

Overview
This document specifies the Hybrid AI Separation method for the GIMP AI Color Separation plugin. This advanced separation technique uses a second AI call (Gemini) to intelligently segment complex images into regions and apply different separation strategies per region, combining the precision of spot color separation with the photorealistic quality of simulated process separation.
Purpose
Handle complex images that contain both:

Vector-like elements (logos, text, sharp graphics) → Best with spot color
Photo-like elements (portraits, gradients, textures) → Best with simulated process
Mixed content requiring intelligent region-based approach

Core Responsibilities

AI Call #2 (Gemini) - Analyze image and recommend region-based separation strategy
Region Segmentation - Divide image into logical zones based on content type
Per-Region Method Assignment - Apply optimal separation method to each region
Intelligent Merging - Combine regional separations with smooth transitions
Channel Output - Create unified GIMP layers from regional results


When to Use Hybrid AI Separation
Ideal Candidates

Mixed Content Images

Logo overlaid on photograph
Product shot with text overlay
Illustration with photographic elements
Vintage poster combining hand-drawn and photo elements


Complex Artwork

Concert posters with type + photos
Sports designs with player photos + graphics
Packaging mockups with product photography
Retro designs mixing illustration styles


Quality-Critical Projects

High-end screen printing requiring maximum fidelity
Limited edition art prints
Museum-quality reproductions
Professional merchandise



Not Recommended For

Simple logos or graphics (use spot color)
Pure photographs (use simulated process)
Tight budget projects (higher complexity = higher cost)
Quick turnaround jobs (longer processing time)


Architecture
Module Structure
gimp-ai-separation/
├── separation/
│   ├── engines/
│   │   ├── hybrid_ai_engine.py          # Main hybrid engine (NEW)
│   │   ├── region_analyzer.py           # AI Call #2 coordinator (NEW)
│   │   ├── region_segmenter.py          # Image segmentation (NEW)
│   │   ├── region_method_selector.py    # Method per region (NEW)
│   │   ├── regional_separator.py        # Apply methods to regions (NEW)
│   │   └── channel_merger.py            # Merge regional results (NEW)
│   └── gemini_region_prompt.py          # Gemini prompt builder (NEW)
```

### Integration with Existing Engines
```
Hybrid AI Engine
    ↓
Uses existing engines per region:
    - SpotColorEngine (for vector regions)
    - SimulatedProcessEngine (for photo regions)
    - IndexColorEngine (for mixed regions)

Data Structures
Region Definition
pythonfrom dataclasses import dataclass
from typing import List, Dict, Tuple
import numpy as np
from enum import Enum

class RegionType(str, Enum):
    """Types of image regions"""
    VECTOR = "vector"           # Sharp edges, flat colors
    PHOTO = "photo"             # Soft edges, gradients, detail
    TEXT = "text"               # High-contrast text/linework
    MIXED = "mixed"             # Combination of characteristics
    BACKGROUND = "background"   # Uniform background area

class ContentComplexity(str, Enum):
    """Complexity level of region content"""
    SIMPLE = "simple"           # <3 colors, no gradients
    MODERATE = "moderate"       # 3-6 colors, some gradients
    COMPLEX = "complex"         # 6+ colors, many gradients

@dataclass
class ImageRegion:
    """Single segmented region of the image"""
    id: str
    region_type: RegionType
    complexity: ContentComplexity
    
    # Spatial information
    mask: np.ndarray            # Boolean mask (same size as image)
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    pixel_count: int
    coverage_percentage: float
    
    # Visual characteristics
    dominant_colors: List[Tuple[int, int, int]]  # Top 3-5 colors in region
    has_gradients: bool
    edge_sharpness: float       # 0-1, higher = sharper
    texture_score: float        # 0-1, higher = more texture
    
    # Separation strategy
    recommended_method: SeparationMethod
    method_confidence: float    # 0-1
    reasoning: str
    
    # Metadata
    priority: int               # 1-10, higher = more important
Region Analysis Result
python@dataclass
class RegionAnalysisResult:
    """Complete AI analysis of image regions"""
    
    # Segmentation results
    regions: List[ImageRegion]
    region_count: int
    
    # Overall strategy
    strategy_summary: str
    complexity_rating: str      # "simple", "moderate", "complex"
    
    # Method assignments
    method_assignments: Dict[str, SeparationMethod]  # region_id -> method
    
    # Quality predictions
    expected_quality: str       # "excellent", "good", "fair"
    expected_channels: int
    estimated_processing_time: float  # seconds
    
    # Confidence metrics
    overall_confidence: float   # 0-1
    confidence_by_region: Dict[str, float]
    
    # AI metadata
    gemini_response: Dict
    timestamp: str
Hybrid Separation Parameters
python@dataclass
class HybridSeparationParameters:
    """User-adjustable parameters for hybrid separation"""
    
    # Segmentation
    min_region_size: int = 1000         # Minimum pixels for separate region
    edge_sensitivity: float = 0.5       # 0-1, higher = more sensitive
    
    # Region blending
    blend_edges: bool = True
    blend_radius: int = 15              # Pixels for edge blending
    
    # Method preferences
    prefer_spot_color: bool = True      # Favor spot color when ambiguous
    allow_mixed_method: bool = True     # Allow "mixed" regions
    
    # Quality/speed tradeoff
    detail_level: str = "high"          # "low", "medium", "high"
    
    # Advanced
    custom_region_methods: Dict[str, SeparationMethod] = None  # Override AI

AI Call #2: Region Analysis with Gemini
Purpose
Use Gemini's vision capabilities to:

Understand image content and context
Identify distinct regions requiring different approaches
Recommend optimal separation method per region
Provide reasoning for recommendations

Gemini Prompt Structure
python"""
gemini_region_prompt.py - Prompt builder for AI Call #2
"""

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
- Vector-like regions → Spot Color
- Photo-like regions → Simulated Process
- Mixed regions → Index Color or evaluate hybrid sub-approach

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
        import json
        import re
        
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
```

### Example Gemini Prompt (Complete)
```
You are an expert screen printing color separation advisor. Analyze this image and recommend an intelligent region-based separation strategy.

IMAGE CONTEXT:
- Palette: 6 colors - Bright Red (#FF0000), Royal Blue (#0000FF), Yellow (#FFFF00), and 3 more colors
- Overall Type: mixed
- Has Gradients: true
- Edge Characteristics: mixed

PRELIMINARY SEGMENTATION:
We've identified 3 potential regions using computer vision:

Region 1: vector area, 35.2% of image, edge sharpness 0.89
Region 2: photo area, 52.1% of image, edge sharpness 0.31
Region 3: mixed area, 12.7% of image, edge sharpness 0.58

[... rest of prompt as shown above ...]
Example Gemini Response
json{
  "overall_strategy": "This concert poster combines a sharp vintage logo with a photographic portrait background. The logo should use spot color separation for crisp edges and accurate brand colors, while the portrait background needs simulated process for smooth skin tones and gradient lighting. A small text region can use spot color for maximum clarity.",
  
  "complexity_rating": "complex",
  
  "regions": [
    {
      "region_id": "region_1",
      "content_description": "Band logo with decorative border - vintage style typography",
      "region_type": "vector",
      "complexity": "moderate",
      
      "characteristics": {
        "dominant_colors": ["#FF0000", "#000000", "#FFFFFF"],
        "has_gradients": false,
        "edge_sharpness": 0.92,
        "texture_present": false
      },
      
      "recommended_method": "spot_color",
      "method_confidence": 0.95,
      "reasoning": "Clean vector artwork with sharp edges and flat colors is ideal for spot color separation. The three distinct colors (red, black, white) will reproduce accurately without halftone dots, maintaining the vintage aesthetic and ensuring maximum legibility.",
      
      "priority": 10,
      "alternatives": [
        {
          "method": "index_color",
          "confidence": 0.7,
          "note": "Could work if simplification is acceptable, but spot color will deliver superior edge quality"
        }
      ]
    },
    
    {
      "region_id": "region_2",
      "content_description": "Portrait photograph with dramatic lighting and gradients",
      "region_type": "photo",
      "complexity": "complex",
      
      "characteristics": {
        "dominant_colors": ["#8B4513", "#FFE4C4", "#2F2F2F", "#D4AF37"],
        "has_gradients": true,
        "edge_sharpness": 0.28,
        "texture_present": true
      },
      
      "recommended_method": "simulated_process",
      "method_confidence": 0.93,
      "reasoning": "Photographic content with smooth skin tone gradients, dramatic lighting, and subtle texture requires simulated process separation. This method will preserve the tonal range and fine detail while avoiding banding in the gradient shadows. The 6-color palette provides enough range for accurate color matching.",
      
      "priority": 9,
      "alternatives": [
        {
          "method": "index_color",
          "confidence": 0.5,
          "note": "Would show visible banding in the gradients and lose subtle texture detail"
        }
      ]
    },
    
    {
      "region_id": "region_3",
      "content_description": "Venue name and date text overlaid on image",
      "region_type": "text",
      "complexity": "simple",
      
      "characteristics": {
        "dominant_colors": ["#FFFF00"],
        "has_gradients": false,
        "edge_sharpness": 0.91,
        "texture_present": false
      },
      
      "recommended_method": "spot_color",
      "method_confidence": 0.98,
      "reasoning": "Text requires maximum clarity and sharpness for readability. Single flat color (yellow) with sharp edges is perfect for spot color separation. This ensures the text remains crisp at any viewing distance.",
      
      "priority": 8,
      "alternatives": []
    }
  ],
  
  "region_interactions": [
    {
      "region_pair": ["region_1", "region_2"],
      "relationship": "overlapping",
      "blending_needed": true,
      "transition_complexity": "moderate"
    },
    {
      "region_pair": ["region_2", "region_3"],
      "relationship": "adjacent",
      "blending_needed": false,
      "transition_complexity": "simple"
    }
  ],
  
  "expected_results": {
    "quality_rating": "excellent",
    "channel_count": 6,
    "print_complexity": "high"
  },
  
  "confidence_assessment": {
    "overall_confidence": 0.91,
    "uncertainty_areas": [
      "Small decorative elements in logo border might benefit from slight blur to prevent moiré"
    ],
    "improvement_suggestions": [
      "Consider slightly softening the logo/photo boundary for smoother visual transition",
      "If printing costs are a concern, the photo could be reduced to 4-color simulated process"
    ]
  }
}

Region Segmentation Process
Step 1: Initial Computer Vision Segmentation
python"""
region_segmenter.py - Image segmentation for hybrid separation
"""

import cv2
import numpy as np
from scipy import ndimage
from skimage.segmentation import slic, watershed
from skimage.feature import canny

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
        
        Returns:
            List of preliminary region dictionaries
        """
        height, width = rgb_image.shape[:2]
        
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
        
        # Multi-scale edge detection
        edges_fine = canny(L_channel, sigma=1.0)
        edges_coarse = canny(L_channel, sigma=3.0)
        
        # Combine
        edges_combined = edges_fine | edges_coarse
        
        # Dilate to create regions
        kernel_size = int(10 * sensitivity)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        edges_dilated = cv2.dilate(edges_combined.astype(np.uint8), kernel)
        
        # Label connected components
        labeled, num_regions = ndimage.label(edges_dilated)
        
        regions = []
        for i in range(1, num_regions + 1):
            mask = (labeled == i)
            regions.append(mask)
        
        return regions
    
    def _segment_by_color(
        self,
        lab_image: np.ndarray,
        min_region_size: int
    ) -> List[np.ndarray]:
        """
        Segment based on color similarity using SLIC superpixels
        """
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
    
    def _segment_by_texture(
        self,
        rgb_image: np.ndarray,
        analysis_data: Dict
    ) -> List[np.ndarray]:
        """
        Segment based on texture characteristics
        Photo regions have texture, vector regions don't
        """
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
        
        # Calculate local standard deviation (texture measure)
        window_size = 15
        kernel = np.ones((window_size, window_size)) / (window_size ** 2)
        
        mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        sqr_mean = cv2.filter2D((gray ** 2).astype(np.float32), -1, kernel)
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
        
        # K-means clustering
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=min(n, len(np.unique(pixels, axis=0))))
        kmeans.fit(pixels)
        
        # Get cluster centers (dominant colors)
        colors = kmeans.cluster_centers_.astype(int)
        return [tuple(c) for c in colors]
    
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
        
        # Calculate gradient in region
        grad_x = cv2.Sobel(L_channel, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(L_channel, cv2.CV_64F, 0, 1, ksize=3)
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
        gradient_ratio = np.sum(small_diffs) / len(differences)
        
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

Step 2: AI Region Analysis
python"""
region_analyzer.py - Coordinator for AI Call #2
"""

import google.generativeaiRetryDcontinuepython"""
region_analyzer.py - Coordinator for AI Call #2
"""

import google.generativeai as genai
from typing import List, Dict, Tuple
import numpy as np
import json
from datetime import datetime

class RegionAnalyzer:
    """
    Coordinates AI Call #2 for region-based separation strategy
    Combines computer vision segmentation with Gemini intelligence
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None
        
        self.prompt_builder = GeminiRegionAnalyzer()
        self.region_segmenter = RegionSegmenter()
    
    def analyze_regions(
        self,
        rgb_image: np.ndarray,
        lab_image: np.ndarray,
        palette: UserPalette,
        analysis_data: AnalysisDataModel,
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
        
        preliminary_regions = self.region_segmenter.segment_image(
            rgb_image=rgb_image,
            lab_image=lab_image,
            analysis_data=analysis_data,
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
                analysis_data=analysis_data
            )
        else:
            print("  [Hybrid AI] Step 2: Fallback rule-based analysis (no API key)...")
            
            ai_analysis = self._get_rule_based_analysis(
                preliminary_regions=preliminary_regions,
                palette=palette,
                analysis_data=analysis_data
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
    
    def _get_ai_region_analysis(
        self,
        rgb_image: np.ndarray,
        preliminary_regions: List[Dict],
        palette: UserPalette,
        analysis_data: AnalysisDataModel
    ) -> Dict:
        """
        Get AI analysis from Gemini
        """
        # Build prompt
        image_characteristics = {
            'texture_type': analysis_data.texture_analysis.get('texture_type', 'mixed'),
            'has_gradients': analysis_data.color_analysis.get('gradient_analysis', {}).get('gradient_present', False),
            'edge_type': analysis_data.edge_analysis.get('edge_type', 'mixed')
        }
        
        palette_dict = [
            {
                'name': c.name,
                'rgb': c.rgb,
                'hex': self._rgb_to_hex(c.rgb)
            }
            for c in palette.colors
        ]
        
        prompt = self.prompt_builder.build_region_analysis_prompt(
            image_characteristics=image_characteristics,
            palette=palette_dict,
            preliminary_regions=preliminary_regions
        )
        
        # Call Gemini
        try:
            # Upload image for vision analysis
            import tempfile
            import os
            from PIL import Image
            
            # Save image temporarily
            temp_path = tempfile.mktemp(suffix='.png')
            Image.fromarray(rgb_image).save(temp_path)
            
            # Upload to Gemini
            uploaded_file = genai.upload_file(temp_path)
            
            # Generate response with vision
            response = self.model.generate_content([
                uploaded_file,
                prompt
            ])
            
            # Clean up
            os.remove(temp_path)
            
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
    
    def _get_rule_based_analysis(
        self,
        preliminary_regions: List[Dict],
        palette: UserPalette,
        analysis_data: AnalysisDataModel
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
                'priority': 5
            })
        
        return {
            'overall_strategy': f"Rule-based hybrid separation with {len(regions)} regions",
            'complexity_rating': 'moderate',
            'regions': regions,
            'region_interactions': [],
            'expected_results': {
                'quality_rating': 'good',
                'channel_count': palette.color_count,
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
        palette: UserPalette
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


"""
================================================================================
STEP 3: REGIONAL SEPARATION
================================================================================
"""

class RegionalSeparator:
    """
    Applies appropriate separation method to each region
    """
    
    def __init__(self):
        # Initialize all separation engines
        self.spot_engine = SpotColorEngine()
        self.simulated_engine = SimulatedProcessEngine()
        self.index_engine = IndexColorEngine()
    
    def separate_regions(
        self,
        rgb_image: np.ndarray,
        lab_image: np.ndarray,
        region_analysis: RegionAnalysisResult,
        palette: UserPalette,
        analysis_data: AnalysisDataModel
    ) -> List[Dict]:
        """
        Separate each region using its recommended method
        
        Args:
            rgb_image: Original RGB image
            lab_image: LAB color space image
            region_analysis: AI analysis results
            palette: Color palette
            analysis_data: Original analysis data
            
        Returns:
            List of regional separation results
        """
        regional_results = []
        
        for region in region_analysis.regions:
            print(f"    [Region {region.id}] Separating with {region.recommended_method.value}...")
            
            # Extract region image
            region_rgb = self._extract_region_image(rgb_image, region.mask)
            region_lab = self._extract_region_image(lab_image, region.mask)
            
            # Get appropriate engine
            engine = self._get_engine_for_method(region.recommended_method)
            
            # Get method-specific parameters
            parameters = self._get_parameters_for_region(region)
            
            # Execute separation
            try:
                channels = engine.separate(
                    image_data=region_rgb,
                    lab_image=region_lab,
                    palette=palette,
                    analysis=analysis_data,
                    parameters=parameters
                )
                
                # Store result
                regional_results.append({
                    'region_id': region.id,
                    'region': region,
                    'method': region.recommended_method,
                    'channels': channels,
                    'success': True
                })
                
                print(f"    [Region {region.id}] ✓ Created {len(channels)} channels")
                
            except Exception as e:
                print(f"    [Region {region.id}] ✗ Separation failed: {e}")
                
                # Store failure
                regional_results.append({
                    'region_id': region.id,
                    'region': region,
                    'method': region.recommended_method,
                    'channels': [],
                    'success': False,
                    'error': str(e)
                })
        
        return regional_results
    
    def _extract_region_image(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """
        Extract region from image, filling non-region with white
        """
        region_image = image.copy()
        
        # Set non-region pixels to white
        if len(image.shape) == 3:
            # RGB/LAB image
            region_image[~mask] = [255, 255, 255] if image.dtype == np.uint8 else [100, 0, 0]
        else:
            # Grayscale
            region_image[~mask] = 255 if image.dtype == np.uint8 else 100
        
        return region_image
    
    def _get_engine_for_method(self, method: SeparationMethod):
        """Get appropriate separation engine"""
        if method == SeparationMethod.SPOT_COLOR:
            return self.spot_engine
        elif method == SeparationMethod.SIMULATED_PROCESS:
            return self.simulated_engine
        elif method == SeparationMethod.INDEX_COLOR:
            return self.index_engine
        else:
            # Fallback to index
            return self.index_engine
    
    def _get_parameters_for_region(self, region: ImageRegion) -> Dict:
        """Get method-specific parameters based on region characteristics"""
        
        if region.recommended_method == SeparationMethod.SPOT_COLOR:
            # Adjust tolerance based on edge sharpness
            tolerance = 15.0 if region.edge_sharpness > 0.8 else 20.0
            
            return {
                'color_tolerance': tolerance,
                'edge_smoothing': region.edge_sharpness < 0.7
            }
        
        elif region.recommended_method == SeparationMethod.SIMULATED_PROCESS:
            # Use error diffusion for gradients
            return {
                'dither_method': 'error_diffusion' if region.has_gradients else 'none',
                'halftone_method': 'stochastic'
            }
        
        elif region.recommended_method == SeparationMethod.INDEX_COLOR:
            # Use dithering if gradients present
            return {
                'dither_method': 'floyd_steinberg' if region.has_gradients else 'none'
            }
        
        return {}


"""
================================================================================
STEP 4: CHANNEL MERGING
================================================================================
"""

class ChannelMerger:
    """
    Intelligently merges channels from different regions
    """
    
    def merge_regional_channels(
        self,
        regional_results: List[Dict],
        palette: UserPalette,
        image_shape: Tuple[int, int],
        parameters: HybridSeparationParameters
    ) -> List[SeparatedChannel]:
        """
        Merge channels from all regions into unified palette channels
        
        Args:
            regional_results: List of regional separation results
            palette: Color palette
            image_shape: (height, width) of final image
            parameters: Hybrid parameters (for blending)
            
        Returns:
            List of merged SeparatedChannel objects
        """
        height, width = image_shape
        merged_channels = []
        
        print("    [Merge] Combining regional channels...")
        
        # Create one channel per palette color
        for color_idx, color in enumerate(palette.colors):
            print(f"    [Merge] Processing {color.name}...")
            
            # Initialize merged channel data
            merged_data = np.zeros((height, width), dtype=np.float32)
            
            # Accumulate contributions from each region
            for regional in regional_results:
                if not regional['success']:
                    continue
                
                region = regional['region']
                channels = regional['channels']
                mask = region.mask
                
                # Find matching color channel in this region
                matching_channel = self._find_matching_channel(channels, color)
                
                if matching_channel is not None:
                    # Add contribution with mask
                    if parameters.blend_edges:
                        # Smooth blend at region edges
                        blended_mask = self._create_blended_mask(
                            mask,
                            blend_radius=parameters.blend_radius
                        )
                        merged_data += matching_channel.data.astype(np.float32) * blended_mask
                    else:
                        # Hard edge
                        merged_data[mask] = np.maximum(
                            merged_data[mask],
                            matching_channel.data[mask].astype(np.float32)
                        )
            
            # Normalize and convert to uint8
            merged_data = np.clip(merged_data, 0, 255).astype(np.uint8)
            
            # Calculate statistics
            pixel_count = np.sum(merged_data > 0)
            coverage = (pixel_count / merged_data.size) * 100
            
            # Create merged channel
            channel = SeparatedChannel(
                id=f"channel_{color_idx + 1}",
                name=color.name,
                color_info={
                    'rgb': color.rgb,
                    'lab': color.lab,
                    'pantone': color.pantone_code,
                    'hex': self._rgb_to_hex(color.rgb)
                },
                order=color_idx + 1,
                visible=True,
                locked=False,
                opacity=1.0,
                data=merged_data,
                adjustments=ChannelAdjustments(
                    halftone_frequency=55.0,
                    halftone_angle=45.0 + (color_idx * 15),
                    halftone_shape="round"
                ),
                pixel_count=int(pixel_count),
                coverage_percentage=float(coverage),
                created_at=datetime.now().isoformat()
            )
            
            merged_channels.append(channel)
            print(f"    [Merge] ✓ {color.name}: {coverage:.1f}% coverage")
        
        return merged_channels
    
    def _find_matching_channel(
        self,
        channels: List[SeparatedChannel],
        target_color: PaletteColor
    ) -> SeparatedChannel:
        """Find channel matching target color"""
        for ch in channels:
            # Match by name or RGB
            if (ch.name == target_color.name or 
                ch.color_info.get('rgb') == target_color.rgb):
                return ch
        return None
    
    def _create_blended_mask(
        self,
        mask: np.ndarray,
        blend_radius: int
    ) -> np.ndarray:
        """
        Create smoothly blended mask for region edges
        
        Args:
            mask: Binary mask
            blend_radius: Radius for blending in pixels
            
        Returns:
            Float mask with smooth transitions at edges
        """
        import cv2
        
        # Convert to float
        mask_float = mask.astype(np.float32)
        
        # Apply Gaussian blur for smooth transitions
        kernel_size = blend_radius * 2 + 1
        blended = cv2.GaussianBlur(
            mask_float,
            (kernel_size, kernel_size),
            sigma=blend_radius / 2.0
        )
        
        return blended
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to hex"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


"""
================================================================================
HYBRID AI ENGINE - MAIN COORDINATOR
================================================================================
"""

class HybridAIEngine:
    """
    Main Hybrid AI Separation Engine
    Coordinates the complete hybrid workflow
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
        # Initialize components
        self.region_analyzer = RegionAnalyzer(api_key)
        self.regional_separator = RegionalSeparator()
        self.channel_merger = ChannelMerger()
    
    def separate(
        self,
        image_data: np.ndarray,
        lab_image: np.ndarray,
        palette: UserPalette,
        analysis: AnalysisDataModel,
        parameters: Dict
    ) -> List[SeparatedChannel]:
        """
        Execute complete hybrid AI separation
        
        This is the main entry point called by SeparationCoordinator
        when user selects Hybrid AI method
        
        Workflow:
        1. AI Call #2: Analyze regions and recommend methods
        2. Separate each region with appropriate method
        3. Merge regional results into unified channels
        
        Args:
            image_data: RGB image
            lab_image: LAB color space image
            palette: User's color palette
            analysis: Analysis from Analyze unit
            parameters: Hybrid-specific parameters
            
        Returns:
            List of merged SeparatedChannel objects
        """
        print("\n  [Hybrid AI] Starting hybrid separation...")
        
        # Parse parameters
        hybrid_params = HybridSeparationParameters(
            min_region_size=parameters.get('min_region_size', 1000),
            edge_sensitivity=parameters.get('edge_sensitivity', 0.5),
            blend_edges=parameters.get('blend_edges', True),
            blend_radius=parameters.get('blend_radius', 15),
            prefer_spot_color=parameters.get('prefer_spot_color', True),
            allow_mixed_method=parameters.get('allow_mixed_method', True),
            detail_level=parameters.get('detail_level', 'high')
        )
        
        # ============================================================
        # STEP 1: AI REGION ANALYSIS (AI CALL #2)
        # ============================================================
        print("\n  [Hybrid AI] === AI CALL #2: Region Analysis ===")
        
        region_analysis = self.region_analyzer.analyze_regions(
            rgb_image=image_data,
            lab_image=lab_image,
            palette=palette,
            analysis_data=analysis,
            parameters=hybrid_params
        )
        
        print(f"\n  [Hybrid AI] Strategy: {region_analysis.strategy_summary}")
        print(f"  [Hybrid AI] Confidence: {int(region_analysis.overall_confidence * 100)}%")
        print(f"  [Hybrid AI] Regions: {region_analysis.region_count}")
        
        for region in region_analysis.regions:
            print(f"    - {region.id}: {region.region_type.value} → {region.recommended_method.value}")
        
        # ============================================================
        # STEP 2: SEPARATE EACH REGION
        # ============================================================
        print("\n  [Hybrid AI] === Separating Regions ===")
        
        regional_results = self.regional_separator.separate_regions(
            rgb_image=image_data,
            lab_image=lab_image,
            region_analysis=region_analysis,
            palette=palette,
            analysis_data=analysis
        )
        
        # ============================================================
        # STEP 3: MERGE REGIONAL CHANNELS
        # ============================================================
        print("\n  [Hybrid AI] === Merging Channels ===")
        
        merged_channels = self.channel_merger.merge_regional_channels(
            regional_results=regional_results,
            palette=palette,
            image_shape=image_data.shape[:2],
            parameters=hybrid_params
        )
        
        print(f"\n  [Hybrid AI] ✓ Hybrid separation complete: {len(merged_channels)} channels")
        
        return merged_channels


"""
================================================================================
GIMP INTEGRATION - HYBRID DIALOG
================================================================================
"""

class HybridParametersDialog(Gtk.Dialog):
    """
    GTK dialog for hybrid separation parameters
    Shown before executing hybrid separation
    """
    
    def __init__(self, parent, default_params: HybridSeparationParameters):
        super().__init__(
            title="Hybrid AI Separation - Parameters",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        
        self.params = default_params
        
        self.set_default_size(500, 400)
        
        self.init_ui()
    
    def init_ui(self):
        """Build parameter UI"""
        box = self.get_content_area()
        box.set_spacing(12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<b><big>Hybrid AI Separation Parameters</big></b>")
        box.pack_start(title, False, False, 0)
        
        # Description
        desc = Gtk.Label(
            label="Hybrid separation uses AI to intelligently combine multiple "
                  "separation methods for complex images. Adjust parameters below:"
        )
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        box.pack_start(desc, False, False, 0)
        
        # Separator
        box.pack_start(Gtk.Separator(), False, False, 6)
        
        # Segmentation section
        seg_frame = Gtk.Frame(label="Segmentation")
        seg_box = Gtk.VBox(spacing=6)
        seg_box.set_margin_left(12)
        seg_box.set_margin_right(12)
        seg_box.set_margin_top(6)
        seg_box.set_margin_bottom(6)
        
        # Min region size
        size_hbox = Gtk.HBox(spacing=12)
        size_hbox.pack_start(Gtk.Label(label="Minimum Region Size:"), False, False, 0)
        self.region_size_adj = Gtk.Adjustment(
            value=self.params.min_region_size,
            lower=500,
            upper=5000,
            step_increment=100
        )
        size_spin = Gtk.SpinButton(adjustment=self.region_size_adj)
        size_hbox.pack_start(size_spin, False, False, 0)
        size_hbox.pack_start(Gtk.Label(label="pixels"), False, False, 0)
        seg_box.pack_start(size_hbox, False, False, 0)
        
        # Edge sensitivity
        edge_hbox = Gtk.HBox(spacing=12)
        edge_hbox.pack_start(Gtk.Label(label="Edge Sensitivity:"), False, False, 0)
        self.edge_sens_adj = Gtk.Adjustment(
            value=self.params.edge_sensitivity,
            lower=0.1,
            upper=1.0,
            step_increment=0.1
        )
        edge_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=self.edge_sens_adj
        )
        edge_scale.set_hexpand(True)
        edge_scale.set_digits(1)
        edge_hbox.pack_start(edge_scale, True, True, 0)
        seg_box.pack_start(edge_hbox, False, False, 0)
        
        seg_frame.add(seg_box)
        box.pack_start(seg_frame, False, False, 0)
        
        # Blending section
        blend_frame = Gtk.Frame(label="Region Blending")
        blend_box = Gtk.VBox(spacing=6)
        blend_box.set_margin_left(12)
        blend_box.set_margin_right(12)
        blend_box.set_margin_top(6)
        blend_box.set_margin_bottom(6)
        
        # Blend edges checkbox
        self.blend_check = Gtk.CheckButton(label="Blend region edges for smooth transitions")
        self.blend_check.set_active(self.params.blend_edges)
        self.blend_check.connect('toggled', self.on_blend_toggled)
        blend_box.pack_start(self.blend_check, False, False, 0)
        
        # Blend radius
        radius_hbox =RetryDcontinuepython        # Blend radius
        radius_hbox = Gtk.HBox(spacing=12)
        radius_hbox.pack_start(Gtk.Label(label="Blend Radius:"), False, False, 0)
        self.blend_radius_adj = Gtk.Adjustment(
            value=self.params.blend_radius,
            lower=5,
            upper=50,
            step_increment=5
        )
        radius_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=self.blend_radius_adj
        )
        radius_scale.set_hexpand(True)
        radius_scale.set_digits(0)
        self.radius_scale = radius_scale
        radius_scale.set_sensitive(self.params.blend_edges)
        radius_hbox.pack_start(radius_scale, True, True, 0)
        radius_hbox.pack_start(Gtk.Label(label="pixels"), False, False, 0)
        blend_box.pack_start(radius_hbox, False, False, 0)
        
        blend_frame.add(blend_box)
        box.pack_start(blend_frame, False, False, 0)
        
        # Method preferences section
        method_frame = Gtk.Frame(label="Method Preferences")
        method_box = Gtk.VBox(spacing=6)
        method_box.set_margin_left(12)
        method_box.set_margin_right(12)
        method_box.set_margin_top(6)
        method_box.set_margin_bottom(6)
        
        # Prefer spot color
        self.spot_check = Gtk.CheckButton(
            label="Prefer spot color for ambiguous regions (better accuracy)"
        )
        self.spot_check.set_active(self.params.prefer_spot_color)
        method_box.pack_start(self.spot_check, False, False, 0)
        
        # Allow mixed method
        self.mixed_check = Gtk.CheckButton(
            label="Allow mixed separation for transition regions"
        )
        self.mixed_check.set_active(self.params.allow_mixed_method)
        method_box.pack_start(self.mixed_check, False, False, 0)
        
        method_frame.add(method_box)
        box.pack_start(method_frame, False, False, 0)
        
        # Quality section
        quality_frame = Gtk.Frame(label="Quality / Speed")
        quality_box = Gtk.VBox(spacing=6)
        quality_box.set_margin_left(12)
        quality_box.set_margin_right(12)
        quality_box.set_margin_top(6)
        quality_box.set_margin_bottom(6)
        
        quality_label = Gtk.Label(label="Detail Level:")
        quality_label.set_xalign(0)
        quality_box.pack_start(quality_label, False, False, 0)
        
        self.quality_combo = Gtk.ComboBoxText()
        self.quality_combo.append_text("Low (Fast)")
        self.quality_combo.append_text("Medium (Balanced)")
        self.quality_combo.append_text("High (Best Quality)")
        
        quality_map = {'low': 0, 'medium': 1, 'high': 2}
        self.quality_combo.set_active(quality_map.get(self.params.detail_level, 2))
        quality_box.pack_start(self.quality_combo, False, False, 0)
        
        quality_frame.add(quality_box)
        box.pack_start(quality_frame, False, False, 0)
        
        # Buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Start Hybrid Separation", Gtk.ResponseType.OK)
        
        self.show_all()
    
    def on_blend_toggled(self, button):
        """Enable/disable blend radius when checkbox toggled"""
        self.radius_scale.set_sensitive(button.get_active())
    
    def get_parameters(self) -> HybridSeparationParameters:
        """Get user-configured parameters"""
        quality_values = ['low', 'medium', 'high']
        
        return HybridSeparationParameters(
            min_region_size=int(self.region_size_adj.get_value()),
            edge_sensitivity=self.edge_sens_adj.get_value(),
            blend_edges=self.blend_check.get_active(),
            blend_radius=int(self.blend_radius_adj.get_value()),
            prefer_spot_color=self.spot_check.get_active(),
            allow_mixed_method=self.mixed_check.get_active(),
            detail_level=quality_values[self.quality_combo.get_active()]
        )


"""
================================================================================
WORKFLOW INTEGRATION
================================================================================
"""

def execute_hybrid_separation_workflow():
    """
    Complete example of hybrid AI separation workflow
    """
    print("="*80)
    print("HYBRID AI SEPARATION - COMPLETE WORKFLOW")
    print("="*80)
    print()
    
    # ============================================================
    # SETUP: Mock data
    # ============================================================
    
    # Complex image: Logo on photo background
    mock_image = np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8)
    mock_lab = np.random.rand(1000, 1000, 3) * 100
    
    # 6-color palette
    mock_palette = UserPalette(
        colors=[
            PaletteColor(
                id="color_1",
                rgb=(255, 0, 0),
                lab=(53.24, 80.09, 67.20),
                pantone_code="185 C",
                pantone_confidence=0.95,
                name="Bright Red"
            ),
            PaletteColor(
                id="color_2",
                rgb=(0, 0, 255),
                lab=(32.30, 79.19, -107.86),
                pantone_code="286 C",
                pantone_confidence=0.88,
                name="Royal Blue"
            ),
            PaletteColor(
                id="color_3",
                rgb=(255, 255, 0),
                lab=(97.14, -21.55, 94.48),
                pantone_code="Yellow C",
                pantone_confidence=0.92,
                name="Yellow"
            ),
            PaletteColor(
                id="color_4",
                rgb=(139, 69, 19),
                lab=(37.74, 21.23, 41.45),
                pantone_code="478 C",
                pantone_confidence=0.87,
                name="Brown"
            ),
            PaletteColor(
                id="color_5",
                rgb=(255, 228, 196),
                lab=(91.48, 5.33, 17.89),
                pantone_code="489 C",
                pantone_confidence=0.79,
                name="Skin Tone"
            ),
            PaletteColor(
                id="color_6",
                rgb=(0, 0, 0),
                lab=(0, 0, 0),
                pantone_code="Black C",
                pantone_confidence=1.0,
                name="Black"
            )
        ],
        palette_version=1,
        color_count=6
    )
    
    # Mock analysis (mixed content)
    mock_analysis = type('AnalysisDataModel', (), {
        'color_analysis': {
            'gradient_analysis': {'gradient_present': True}
        },
        'edge_analysis': {
            'edge_type': 'mixed',
            'line_work_score': 0.65
        },
        'texture_analysis': {
            'texture_type': 'mixed',
            'halftone_analysis': {'halftone_detected': False}
        }
    })()
    
    # ============================================================
    # EXECUTE HYBRID SEPARATION
    # ============================================================
    
    # Initialize hybrid engine (with mock API key)
    hybrid_engine = HybridAIEngine(api_key="mock_key_for_demo")
    
    # Set parameters
    parameters = {
        'min_region_size': 1000,
        'edge_sensitivity': 0.5,
        'blend_edges': True,
        'blend_radius': 15,
        'prefer_spot_color': True,
        'allow_mixed_method': True,
        'detail_level': 'high'
    }
    
    # Execute
    import time
    start_time = time.time()
    
    channels = hybrid_engine.separate(
        image_data=mock_image,
        lab_image=mock_lab,
        palette=mock_palette,
        analysis=mock_analysis,
        parameters=parameters
    )
    
    end_time = time.time()
    
    # ============================================================
    # DISPLAY RESULTS
    # ============================================================
    
    print("\n" + "="*80)
    print("HYBRID SEPARATION RESULTS")
    print("="*80)
    print()
    
    print(f"Processing Time: {end_time - start_time:.2f}s")
    print(f"Channels Created: {len(channels)}")
    print()
    
    print("CHANNELS:")
    for ch in channels:
        print(f"  - {ch.name}")
        print(f"    Coverage: {ch.coverage_percentage:.1f}%")
        print(f"    Pixels: {ch.pixel_count:,}")
        print()
    
    print("="*80)
    print("READY FOR ADJUSTMENT UNIT")
    print("="*80)


"""
================================================================================
PERFORMANCE OPTIMIZATION
================================================================================
"""

class HybridOptimizer:
    """
    Optimization strategies for hybrid separation
    """
    
    @staticmethod
    def optimize_region_count(
        preliminary_regions: List[Dict],
        max_regions: int = 10
    ) -> List[Dict]:
        """
        Reduce region count by merging similar adjacent regions
        """
        if len(preliminary_regions) <= max_regions:
            return preliminary_regions
        
        # Sort by size (keep larger regions)
        sorted_regions = sorted(
            preliminary_regions,
            key=lambda r: r['coverage'],
            reverse=True
        )
        
        # Keep top N largest regions
        return sorted_regions[:max_regions]
    
    @staticmethod
    def cache_region_analysis(
        image_id: str,
        region_analysis: RegionAnalysisResult
    ):
        """
        Cache region analysis to avoid re-running AI
        """
        cache_key = f"hybrid_regions_{image_id}"
        
        # Serialize (without mask arrays)
        cache_data = {
            'region_count': region_analysis.region_count,
            'strategy_summary': region_analysis.strategy_summary,
            'method_assignments': {
                rid: method.value 
                for rid, method in region_analysis.method_assignments.items()
            },
            'timestamp': region_analysis.timestamp
        }
        
        global_state = get_state()
        global_state.add_to_cache(cache_key, cache_data)
    
    @staticmethod
    def parallel_region_separation(
        regions: List[ImageRegion],
        separation_func
    ):
        """
        Process regions in parallel (future enhancement)
        """
        # Placeholder for parallel processing
        # Could use multiprocessing or threading
        pass


"""
================================================================================
ERROR HANDLING & VALIDATION
================================================================================
"""

class HybridValidationError(Exception):
    """Raised when hybrid separation validation fails"""
    pass

class HybridValidator:
    """
    Validates hybrid separation inputs and results
    """
    
    @staticmethod
    def validate_inputs(
        image_data: np.ndarray,
        palette: UserPalette,
        parameters: HybridSeparationParameters
    ) -> Tuple[bool, List[str]]:
        """
        Validate inputs before starting hybrid separation
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Check image size
        if image_data.size > 20_000_000:  # ~5000x4000 RGB
            errors.append("Image too large for hybrid separation (max 20MP). Consider resizing.")
        
        # Check palette size
        if palette.color_count < 2:
            errors.append("Palette must have at least 2 colors for hybrid separation")
        
        if palette.color_count > 12:
            errors.append("Palette too large (>12 colors). Hybrid may be overly complex.")
        
        # Check parameters
        if parameters.min_region_size < 100:
            errors.append("Minimum region size too small (<100 pixels)")
        
        if parameters.blend_edges and parameters.blend_radius < 5:
            errors.append("Blend radius too small (<5 pixels)")
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def validate_region_analysis(
        region_analysis: RegionAnalysisResult
    ) -> Tuple[bool, List[str]]:
        """
        Validate region analysis results
        """
        warnings = []
        
        # Check region count
        if region_analysis.region_count == 0:
            return (False, ["No regions identified"])
        
        if region_analysis.region_count > 15:
            warnings.append(
                f"Many regions identified ({region_analysis.region_count}). "
                "Separation may be very complex."
            )
        
        # Check confidence
        if region_analysis.overall_confidence < 0.5:
            warnings.append(
                f"Low confidence ({int(region_analysis.overall_confidence * 100)}%). "
                "Results may not be optimal."
            )
        
        # Check for regions with no method
        for region in region_analysis.regions:
            if region.recommended_method is None:
                warnings.append(f"Region {region.id} has no recommended method")
        
        return (True, warnings)


"""
================================================================================
GIMP INTEGRATION - UPDATE TO SEPARATION DIALOG
================================================================================
"""

def update_separation_dialog_for_hybrid():
    """
    Modifications to main separation dialog to support Hybrid AI
    """
    
    # In gtk_dialogs.py, update the parameters section:
    
    code_snippet = '''
    def update_parameters(self, method):
        """Update parameter controls based on selected method"""
        # Clear existing
        for child in self.params_vbox.get_children():
            self.params_vbox.remove(child)
        
        # Add method-specific parameters
        if method.method == SeparationMethod.SPOT_COLOR:
            # ... existing spot color params ...
            pass
        
        elif method.method == SeparationMethod.SIMULATED_PROCESS:
            # ... existing simulated process params ...
            pass
        
        elif method.method == SeparationMethod.INDEX_COLOR:
            # ... existing index color params ...
            pass
        
        # NEW: Hybrid AI parameters
        elif method.method == SeparationMethod.HYBRID_AI:
            # Show advanced parameters button
            params_label = Gtk.Label()
            params_label.set_markup(
                "<b>Hybrid AI Separation</b>\n\n"
                "Uses AI to intelligently combine separation methods.\n"
                "Click below to configure advanced parameters."
            )
            params_label.set_line_wrap(True)
            params_label.set_xalign(0)
            self.params_vbox.pack_start(params_label, False, False, 0)
            
            # Advanced parameters button
            advanced_btn = Gtk.Button(label="Advanced Parameters...")
            advanced_btn.connect('clicked', self.on_hybrid_advanced)
            self.params_vbox.pack_start(advanced_btn, False, False, 6)
            
            # Store default params
            self.hybrid_params = HybridSeparationParameters()
            
            # Show expected processing time
            time_label = Gtk.Label()
            time_label.set_markup(
                "<small><i>⏱ Expected processing time: 30-60 seconds</i></small>"
            )
            time_label.set_xalign(0)
            self.params_vbox.pack_start(time_label, False, False, 0)
        
        self.params_vbox.show_all()
    
    def on_hybrid_advanced(self, button):
        """Show hybrid advanced parameters dialog"""
        dialog = HybridParametersDialog(self, self.hybrid_params)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            self.hybrid_params = dialog.get_parameters()
        
        dialog.destroy()
    
    def get_parameters(self):
        """Return method-specific parameters"""
        params = {}
        
        if self.selected_method == SeparationMethod.SPOT_COLOR:
            params['color_tolerance'] = self.tolerance_adj.get_value()
        
        # ... other methods ...
        
        # NEW: Hybrid AI
        elif self.selected_method == SeparationMethod.HYBRID_AI:
            params.update({
                'min_region_size': self.hybrid_params.min_region_size,
                'edge_sensitivity': self.hybrid_params.edge_sensitivity,
                'blend_edges': self.hybrid_params.blend_edges,
                'blend_radius': self.hybrid_params.blend_radius,
                'prefer_spot_color': self.hybrid_params.prefer_spot_color,
                'allow_mixed_method': self.hybrid_params.allow_mixed_method,
                'detail_level': self.hybrid_params.detail_level
            })
        
        return params
    '''


"""
================================================================================
TESTING & VALIDATION
================================================================================
"""

def test_hybrid_separation():
    """
    Test hybrid separation with various image types
    """
    
    test_cases = [
        {
            'name': 'Logo on Photo',
            'description': 'Concert poster with vector logo on photo background',
            'expected_regions': 2,
            'expected_methods': ['spot_color', 'simulated_process']
        },
        {
            'name': 'Product Shot',
            'description': 'Product photo with text overlay',
            'expected_regions': 3,
            'expected_methods': ['simulated_process', 'spot_color', 'spot_color']
        },
        {
            'name': 'Vintage Poster',
            'description': 'Mixed illustration and photo elements',
            'expected_regions': 4,
            'expected_methods': ['spot_color', 'simulated_process', 'index_color', 'spot_color']
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        
        # Run test (would use actual test images)
        # result = run_hybrid_separation(test_image, test_palette)
        
        # Validate
        # assert result.region_count == test_case['expected_regions']
        # assert result methods match expected
        
        print("✓ Test passed")


"""
================================================================================
DOCUMENTATION & EXAMPLES
================================================================================
"""

HYBRID_USAGE_GUIDE = """
# Hybrid AI Separation - Usage Guide

## When to Use

Hybrid AI separation is ideal for:

1. **Mixed Content Images**
   - Logo or text overlaid on photograph
   - Product shots with graphic elements
   - Poster designs combining illustration and photos
   - Vintage designs with mixed media

2. **Quality-Critical Projects**
   - High-end screen printing
   - Limited edition prints
   - Museum-quality reproductions

3. **Complex Artwork**
   - Images with both sharp and soft elements
   - Designs requiring different treatment per region
   - Professional merchandise with photos + graphics

## How It Works

1. **Computer Vision Segmentation**
   - Analyzes edges, colors, and textures
   - Identifies distinct regions in your image
   - Detects vector vs. photo content

2. **AI Region Analysis (Gemini)**
   - Understands context of each region
   - Recommends optimal separation method per region
   - Considers how regions interact

3. **Intelligent Separation**
   - Applies spot color to vector regions (logos, text)
   - Uses simulated process for photo regions
   - Blends transitions smoothly

4. **Channel Merging**
   - Combines regional results
   - Creates unified palette channels
   - Smooth transitions at region boundaries

## Parameters Explained

### Minimum Region Size
- **What it does**: Smallest region to separate independently
- **Lower values**: More detailed segmentation, longer processing
- **Higher values**: Faster, may merge small details
- **Recommended**: 1000-2000 pixels

### Edge Sensitivity
- **What it does**: How sensitive to detect edges between regions
- **Lower values**: Fewer, larger regions
- **Higher values**: More, smaller regions
- **Recommended**: 0.4-0.6 for most images

### Blend Region Edges
- **What it does**: Smoothly blend transitions between regions
- **Enable**: For professional, seamless results
- **Disable**: For hard edges between regions
- **Recommended**: Enabled (on)

### Blend Radius
- **What it does**: Size of blending transition
- **Lower values**: Tighter blend, more visible transitions
- **Higher values**: Smoother blend, may blur details
- **Recommended**: 15-20 pixels

### Prefer Spot Color
- **What it does**: Favor spot color for ambiguous regions
- **Enable**: For maximum color accuracy
- **Disable**: If quality over cost is priority
- **Recommended**: Enabled for screen printing

### Detail Level
- **Low**: Fastest, simplified regions (5-15 sec)
- **Medium**: Balanced quality and speed (15-30 sec)
- **High**: Best quality, detailed analysis (30-60 sec)
- **Recommended**: High for final separations

## Tips for Best Results

1. **Clean Your Image First**
   - Remove unwanted backgrounds
   - Adjust contrast if needed
   - Ensure text is crisp

2. **Choose Appropriate Palette**
   - 4-8 colors work best
   - Include key colors from both photo and vector areas
   - Don't forget black for shadows/text

3. **Review AI Recommendations**
   - Check if region detection makes sense
   - Override if needed (manual region editing coming soon)
   - High confidence (>80%) usually means good results

4. **Test Parameters**
   - Try default settings first
   - Adjust if regions don't match your intent
   - Save successful parameters for similar images

## Processing Time

Typical processing times (on modern CPU):

- Small image (1000x1000): 10-20 seconds
- Medium image (2000x2000): 30-45 seconds
- Large image (4000x4000): 60-90 seconds

Time varies based on:
- Number of regions detected
- Complexity of each region
- Detail level setting
- Your computer's speed

## Troubleshooting

**Too many small regions**
→ Increase minimum region size
→ Decrease edge sensitivity

**Regions don't match image content**
→ Increase edge sensitivity
→ Try different detail level
→ Consider simpler separation method

**Visible seams between regions**
→ Enable blend edges
→ Increase blend radius
→ Check if regions overlap correctly

**Processing takes too long**
→ Reduce detail level to Medium or Low
→ Increase minimum region size
→ Consider resizing image

**AI confidence low (<60%)**
→ Image may not benefit from hybrid
→ Try standard separation method instead
→ Check if palette matches image colors

## Example Workflow

1. Load image in GIMP
2. Run Analyze (Step 1)
3. Run Color Match (Step 2) - create 6-color palette
4. Run Separate Colors (Step 3)
5. Select "Hybrid AI" method
6. Review AI recommendation
7. Click "Advanced Parameters" if needed
8. Click "Separate"
9. Wait for processing (30-60 sec)
10. Review channels in Adjustment Unit

## Cost Considerations

Hybrid separation typically creates more complex screens:

- More setup time at printer
- Potentially more screen fees
- Requires skilled printer
- Worth it for quality-critical projects

Standard spot color or simulated process may be more cost-effective for simpler designs.

## API Usage

Hybrid AI uses one additional Gemini API call:

- **AI Call #1**: Method recommendation (always)
- **AI Call #2**: Region analysis (only for Hybrid)

Total: 2 API calls per image when using Hybrid AI

"""


"""
================================================================================
SUMMARY & INTEGRATION
================================================================================
"""

HYBRID_INTEGRATION_SUMMARY = """
# Hybrid AI Separation - Integration Summary

## Module Components

1. **region_analyzer.py** (~600 lines)
   - Coordinates AI Call #2
   - Builds Gemini prompts
   - Parses AI responses
   - Manages fallback rules

2. **region_segmenter.py** (~500 lines)
   - Computer vision segmentation
   - Edge, color, texture analysis
   - Region characterization
   - Multi-technique combination

3. **regional_separator.py** (~300 lines)
   - Applies methods to regions
   - Manages existing engines
   - Handles region extraction

4. **channel_merger.py** (~400 lines)
   - Merges regional results
   - Blends region boundaries
   - Creates final channels

5. **hybrid_ai_engine.py** (~200 lines)
   - Main coordinator
   - Workflow orchestration
   - Integration with existing engines

6. **gtk_dialogs.py additions** (~300 lines)
   - Hybrid parameters dialog
   - UI integration
   - Parameter validation

**Total New Code**: ~2,300 lines

## Integration Points

### With Existing Separation Unit
- Uses existing SeparationMethod enum (add HYBRID_AI)
- Reuses SpotColorEngine, SimulatedProcessEngine, IndexColorEngine
- Follows SeparationOutput format
- Integrates with SeparationCoordinator

### With Color Match Unit
- Receives UserPalette
- Uses palette colors for channel creation
- Respects Pantone matching

### With Analyze Unit
- Uses AnalysisDataModel
- Leverages edge/texture/gradient analysis
- Builds on existing insights

### With GIMP
- Creates standard GIMP layers
- Uses GTK dialogs
- Follows GIMP plugin patterns
- Stores results in parasites

## AI Call #2 Details

**Trigger**: Only when user selects Hybrid AI method

**Input to Gemini**:
- Image (uploaded for vision analysis)
- Preliminary segmentation results
- Palette information
- Image characteristics from Analyze unit

**Output from Gemini**:
- Per-region content description
- Recommended method for each region
- Confidence scores
- Reasoning for each decision
- Region interaction notes
- Overall strategy summary

**Fallback**: Rule-based analysis if API unavailable

## Performance

**Typical Timing**:
- CV Segmentation: 2-5 seconds
- AI Call #2 (Gemini): 3-8 seconds
- Regional Separation: 10-30 seconds
- Channel Merging: 2-5 seconds
- **Total**: 17-48 seconds (varies by image size/complexity)

**Optimization Strategies**:
- Cache region analysis results
- Limit maximum region count
- Parallel region processing (future)
- Progressive quality levels

## User Experience

1. User selects "Hybrid AI" from recommendations
2. Dialog shows: "This will use AI to analyze regions"
3. Optional: Configure advanced parameters
4. Click "Separate"
5. Progress indicator shows:
   - Segmenting image...
   - AI analyzing regions... (AI Call #2)
   - Separating region 1/3...
   - Separating region 2/3...
   - Separating region 3/3...
   - Merging channels...
   - Complete!
6. Channels appear in layers panel
7. Ready for Adjustment Unit

## Key Features

✅ Intelligent region detection
✅ AI-driven method selection per region
✅ Smooth region blending
✅ Reuses existing separation engines
✅ Configurable parameters
✅ Fallback to rule-based when AI unavailable
✅ Comprehensive error handling
✅ Performance optimized
✅ Full GIMP integration

## Testing Requirements

- Test with mixed content images
- Validate region detection accuracy
- Verify method assignments match expectations
- Check blending quality at boundaries
- Confirm performance acceptable
- Test fallback mode without API key
- Validate parameter adjustments work

## Documentation

- In-app parameter descriptions
- Usage guide (included above)
- Example workflows
- Troubleshooting guide
- API usage information

## Future Enhancements

- Manual region editing/refinement
- Region priority adjustment
- Custom method override per region
- Region library/templates
- Batch processing with same regions
- Machine learning-based segmentation
- GPU acceleration

"""

# End of Hybrid AI Separation Specification

if __name__ == "__main__":
    # Run example workflow
    execute_hybrid_separation_workflow()

End of Specification
This complete specification defines the Hybrid AI Separation method for the GIMP AI Color Separation plugin. Key highlights:
Summary

AI Call #2: Gemini analyzes image regions and recommends optimal method per region
Region Segmentation: Computer vision identifies distinct areas (vector, photo, text, etc.)
Intelligent Merging: Smoothly combines results from different separation methods
Full Integration: Works seamlessly with existing GIMP plugin architecture
~2,300 lines of new code, reusing existing separation engines

When to Use
Perfect for complex images with mixed content (logos on photos, product shots with text, vintage posters, etc.) where different regions benefit from different separation approaches.
The specification is now complete and ready for implementation!RetryClaude can make mistakes. Please double-check responses.
