# GIMP AI Color Separation Plugin - Separation Module Specification
**Version:** 1.0-GIMP  
**Date:** January 2025  
**Status:** Complete Draft for Review

---

## Overview

The Separation module is the third and final component of the AI Color Separation GIMP plugin. It receives analysis data and palette from the previous steps, uses AI to recommend optimal separation methods, allows user selection, and executes the chosen separation strategy to create GIMP layers ready for screen printing.

### Core Responsibilities
1. **AI Method Recommendation (AI Call #1)** - Analyze image + palette to recommend best separation approach
2. **User Selection Interface** - Present recommendations and handle user choice/override
3. **Execute Separation** - Run selected method (with optional AI Call #2 for Hybrid)
4. **Output Layers** - Create properly configured GIMP layers with halftone settings

---

## Architecture Changes from Standalone

### What Stays (80% of existing code)
- ✅ All 6 separation engine algorithms
- ✅ AI method recommendation logic
- ✅ Scoring and evaluation systems
- ✅ Color matching algorithms
- ✅ Region-based separation (Hybrid)
- ✅ Channel statistics calculations

### What Changes
- ❌ Custom data structures → GIMP layers
- ❌ File I/O → GIMP image buffers
- ❌ Custom UI → GTK3 dialogs
- ❌ Standalone workflow → Plugin integration
- ✅ Direct layer creation in GIMP

### What's Simplified
- Fewer separation methods (focus on 3 core: Spot, Simulated, Index)
- Optional advanced methods (CMYK, RGB, Hybrid) for pro users
- Direct integration with GIMP's color management

---

## Module Structure

```
gimp-ai-separation/
├── separation/
│   ├── __init__.py
│   ├── separation_plugin.py          # GIMP plugin wrapper (NEW)
│   ├── method_analyzer.py            # AI Call #1: Recommend methods (EXISTING, adapted)
│   ├── separation_coordinator.py     # Route to engines (EXISTING, adapted)
│   ├── engines/
│   │   ├── spot_color_engine.py      # Spot color separation (EXISTING)
│   │   ├── simulated_process_engine.py # Photo separation (EXISTING)
│   │   ├── index_color_engine.py     # Index/quantized (EXISTING)
│   │   ├── cmyk_engine.py            # CMYK (EXISTING - optional)
│   │   ├── rgb_engine.py             # RGB fallback (EXISTING - optional)
│   │   └── hybrid_ai_engine.py       # AI Call #2: Region-based (EXISTING - advanced)
│   └── gtk_dialogs.py                # GTK UI components (NEW)
```

---

## GIMP Plugin Integration

### Plugin Registration

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
separation_plugin.py - GIMP interface for Separation module
"""

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Gegl', '0.4')
from gi.repository import Gimp, Gtk, GObject, GLib, Gegl
import numpy as np
import json
import sys
import os

# Add plugin directory to path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_dir)

from separation.method_analyzer import AIMethodAnalyzer
from separation.separation_coordinator import SeparationCoordinator
from separation.gtk_dialogs import SeparationDialog

class SeparationPlugin(Gimp.PlugIn):
    """GIMP plugin wrapper for Separation module"""
    
    def do_query_procedures(self):
        """Register procedures with GIMP"""
        return ['ai-separation-separate']
    
    def do_create_procedure(self, name):
        """Create procedure definition"""
        procedure = Gimp.ImageProcedure.new(
            self, name,
            Gimp.PDBProcType.PLUGIN,
            self.run, None
        )
        
        procedure.set_menu_label("Separate Colors (Step 3)")
        procedure.add_menu_path('<Image>/Filters/AI Separation/')
        
        procedure.set_documentation(
            "AI-powered color separation",
            "Separate image into screen-printable layers using AI-recommended methods",
            name
        )
        
        procedure.set_attribution(
            "Your Name",
            "Copyright 2025",
            "2025"
        )
        
        return procedure
    
    def run(self, procedure, run_mode, image, n_drawables, drawables, config, data):
        """Execute separation"""
        try:
            # Check for required data from previous steps
            analysis_data = self.get_parasite_data(image, "ai-separation-analysis")
            palette_data = self.get_parasite_data(image, "ai-separation-palette")
            
            if not analysis_data:
                Gimp.message("Please run 'Analyze Image (Step 1)' first")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error("Analysis data not found")
                )
            
            if not palette_data:
                Gimp.message("Please run 'Color Match (Step 2)' first")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error("Palette data not found")
                )
            
            # Get Gemini API key for method recommendation
            api_key = self.get_api_key()
            
            # Initialize analyzers
            method_analyzer = AIMethodAnalyzer(api_key)
            
            # Get AI recommendations
            Gimp.progress_init("Analyzing separation methods...")
            recommendations = method_analyzer.analyze_and_recommend(
                image=image,
                drawable=drawables[0],
                analysis_data=analysis_data,
                palette_data=palette_data
            )
            
            # Show dialog with recommendations
            dialog = SeparationDialog(
                image=image,
                drawable=drawables[0],
                recommendations=recommendations,
                palette=palette_data['colors']
            )
            
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                # Get user's selected method
                selected_method = dialog.get_selected_method()
                parameters = dialog.get_parameters()
                
                # Execute separation
                Gimp.progress_init(f"Separating using {selected_method}...")
                
                coordinator = SeparationCoordinator(api_key)
                success = coordinator.execute_separation(
                    image=image,
                    drawable=drawables[0],
                    method=selected_method,
                    palette=palette_data['colors'],
                    analysis_data=analysis_data,
                    parameters=parameters
                )
                
                if success:
                    Gimp.message("Separation complete! Check layers panel.")
                    dialog.destroy()
                    return procedure.new_return_values(
                        Gimp.PDBStatusType.SUCCESS,
                        GLib.Error()
                    )
                else:
                    Gimp.message("Separation failed. See error console.")
                    dialog.destroy()
                    return procedure.new_return_values(
                        Gimp.PDBStatusType.EXECUTION_ERROR,
                        GLib.Error("Separation execution failed")
                    )
            else:
                dialog.destroy()
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CANCEL,
                    GLib.Error("User cancelled")
                )
                
        except Exception as e:
            import traceback
            error_msg = f"Separation failed: {str(e)}\n{traceback.format_exc()}"
            Gimp.message(error_msg)
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(str(e))
            )
    
    def get_parasite_data(self, image, parasite_name):
        """Retrieve data from image parasite"""
        parasite = image.get_parasite(parasite_name)
        if parasite:
            data = parasite.get_data().decode('utf-8')
            return json.loads(data)
        return None
    
    def get_api_key(self):
        """Get Gemini API key from GIMP config"""
        config_dir = os.path.join(
            GLib.get_user_config_dir(),
            'GIMP', '3.0', 'ai-separation'
        )
        key_file = os.path.join(config_dir, 'gemini_api.key')
        
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                return f.read().strip()
        return None

Gimp.main(SeparationPlugin.__gtype__, sys.argv)
```

---

## Data Structures

### Separation Methods Enum

```python
from enum import Enum

class SeparationMethod(str, Enum):
    """Available separation methods"""
    SPOT_COLOR = "spot_color"           # Best for: 2-6 flat colors
    SIMULATED_PROCESS = "simulated_process"  # Best for: Photos, gradients
    INDEX_COLOR = "index_color"         # Best for: 6-12 colors, balanced
    CMYK = "cmyk"                       # Optional: Standard 4-color
    RGB = "rgb"                         # Optional: Fallback only
    HYBRID_AI = "hybrid_ai"             # Advanced: Region-based AI
```

### Method Recommendation Structure

```python
@dataclass
class MethodRecommendation:
    """AI recommendation for a separation method"""
    method: SeparationMethod
    method_name: str
    score: float              # 0-100
    confidence: float         # 0-1
    reasoning: str
    
    strengths: List[str]
    limitations: List[str]
    best_for: str
    
    expected_results: Dict    # channel_count, quality, complexity, cost
    palette_utilization: Dict # colors_used, percentage
```

---

## AI Method Analyzer (AI CALL #1)

### Purpose
Analyze the combination of image characteristics (from Analyze unit) and palette (from Color Match unit) to recommend the optimal separation method(s).

### Implementation

```python
"""
method_analyzer.py - AI Call #1: Method recommendation
"""

import google.generativeai as genai
from typing import Dict, List
import numpy as np

class AIMethodAnalyzer:
    """
    AI-powered method recommendation system
    Uses Gemini to analyze image + palette and suggest best approach
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
    
    def analyze_and_recommend(
        self,
        image,
        drawable,
        analysis_data: Dict,
        palette_data: Dict
    ) -> Dict:
        """
        Main AI analysis: Recommend separation methods
        
        Args:
            image: GIMP image
            drawable: Active layer
            analysis_data: Results from Analyze unit
            palette_data: Palette from Color Match unit
            
        Returns:
            Dictionary with recommendations
        """
        # Build context for AI
        context = self._build_analysis_context(
            analysis_data,
            palette_data
        )
        
        # If AI available, get recommendation
        if self.model:
            ai_recommendations = self._get_ai_recommendations(context)
        else:
            # Fallback to rule-based
            ai_recommendations = self._get_rule_based_recommendations(context)
        
        # Score and rank all methods
        scored_methods = self._score_all_methods(context, ai_recommendations)
        
        return {
            'recommended': scored_methods[0],
            'alternatives': scored_methods[1:3],
            'all_methods': scored_methods
        }
    
    def _build_analysis_context(
        self,
        analysis_data: Dict,
        palette_data: Dict
    ) -> Dict:
        """Build context dictionary for method evaluation"""
        return {
            'color_count': len(palette_data['colors']),
            'palette_colors': palette_data['colors'],
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
            print(f"AI recommendation failed: {e}")
            return self._get_rule_based_recommendations(context)
    
    def _build_recommendation_prompt(self, context: Dict) -> str:
        """Build prompt for Gemini AI method recommendation"""
        
        palette_summary = f"{context['color_count']} colors: " + ", ".join(
            [f"{c['name']} (RGB: {c['rgb']})" for c in context['palette_colors'][:3]]
        )
        
        prompt = f"""You are an expert screen printing color separation advisor. Analyze this image and recommend the best separation method.

IMAGE CHARACTERISTICS:
- Palette: {palette_summary}
- Edge Type: {context['image_characteristics']['edge_type']}
- Has Gradients: {context['image_characteristics']['has_gradients']}
- Texture Type: {context['image_characteristics']['texture_type']}
- Line Work Score: {context['image_characteristics']['line_work_score']:.2f}
- Total Unique Colors: {context['image_characteristics']['total_colors']}
- Complexity: {context['image_characteristics']['complexity']:.2f}

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
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    
    def _get_rule_based_recommendations(self, context: Dict) -> Dict:
        """Fallback rule-based recommendations when AI unavailable"""
        
        color_count = context['color_count']
        chars = context['image_characteristics']
        
        # Simple rule-based scoring
        if color_count <= 6 and chars['edge_type'] == 'sharp' and not chars['has_gradients']:
            primary = 'spot_color'
        elif chars['texture_type'] == 'photo' and chars['has_gradients']:
            primary = 'simulated_process'
        elif 6 <= color_count <= 12:
            primary = 'index_color'
        else:
            primary = 'simulated_process'
        
        return {
            'recommended': {
                'method': primary,
                'score': 80,
                'confidence': 0.8,
                'reasoning': 'Rule-based recommendation',
                'strengths': ['Suitable for image type'],
                'limitations': ['AI analysis unavailable'],
                'expected_channels': color_count,
                'quality': 'good'
            },
            'alternatives': []
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
            methods.append(MethodRecommendation(
                method=SeparationMethod(rec['method']),
                method_name=rec['method'].replace('_', ' ').title(),
                score=rec['score'],
                confidence=rec['confidence'],
                reasoning=rec['reasoning'],
                strengths=rec['strengths'],
                limitations=rec['limitations'],
                best_for=self._get_best_for_text(rec['method']),
                expected_results={
                    'channel_count': rec['expected_channels'],
                    'quality': rec['quality'],
                    'complexity': self._estimate_complexity(rec['method']),
                    'cost': self._estimate_cost(rec['expected_channels'])
                },
                palette_utilization={
                    'colors_used': rec['expected_channels'],
                    'colors_total': context['color_count'],
                    'percentage': (rec['expected_channels'] / context['color_count'] * 100)
                }
            ))
        
        # Add alternatives
        for alt in ai_recommendations.get('alternatives', []):
            methods.append(MethodRecommendation(
                method=SeparationMethod(alt['method']),
                method_name=alt['method'].replace('_', ' ').title(),
                score=alt['score'],
                confidence=alt['confidence'],
                reasoning=alt['reasoning'],
                strengths=alt['strengths'],
                limitations=alt['limitations'],
                best_for=self._get_best_for_text(alt['method']),
                expected_results={
                    'channel_count': alt['expected_channels'],
                    'quality': alt['quality'],
                    'complexity': self._estimate_complexity(alt['method']),
                    'cost': self._estimate_cost(alt['expected_channels'])
                },
                palette_utilization={
                    'colors_used': alt['expected_channels'],
                    'colors_total': context['color_count'],
                    'percentage': (alt['expected_channels'] / context['color_count'] * 100)
                }
            ))
        
        # Sort by score
        methods.sort(key=lambda x: x.score, reverse=True)
        
        return methods
    
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
```

---

## GTK Dialog Implementation

### Main Separation Dialog

```python
"""
gtk_dialogs.py - GTK UI for Separation selection
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import numpy as np

class SeparationDialog(Gtk.Dialog):
    """Main separation method selection dialog"""
    
    def __init__(self, image, drawable, recommendations, palette):
        super().__init__(
            title="AI Color Separation - Method Selection",
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        
        self.image = image
        self.drawable = drawable
        self.recommendations = recommendations
        self.palette = palette
        self.selected_method = recommendations['recommended'].method
        
        self.set_default_size(800, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """Build the UI"""
        box = self.get_content_area()
        box.set_spacing(12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Header
        header = Gtk.Label()
        header.set_markup("<b><big>Choose Separation Method</big></b>")
        box.pack_start(header, False, False, 0)
        
        # AI Recommendation Section
        rec_frame = self.create_recommendation_section()
        box.pack_start(rec_frame, False, False, 0)
        
        # Method Selection
        methods_frame = self.create_methods_section()
        box.pack_start(methods_frame, True, True, 0)
        
        # Parameters (method-specific)
        self.params_frame = self.create_parameters_section()
        box.pack_start(self.params_frame, False, False, 0)
        
        # Buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Separate", Gtk.ResponseType.OK)
        
        self.show_all()
    
    def create_recommendation_section(self):
        """Create AI recommendation display"""
        frame = Gtk.Frame(label="AI Recommendation")
        frame.set_margin_top(6)
        
        vbox = Gtk.VBox(spacing=6)
        vbox.set_margin_left(12)
        vbox.set_margin_right(12)
        vbox.set_margin_top(6)
        vbox.set_margin_bottom(6)
        
        rec = self.recommendations['recommended']
        
        # Method name and confidence
        hbox = Gtk.HBox(spacing=12)
        
        method_label = Gtk.Label()
        method_label.set_markup(f"<b>{rec.method_name}</b>")
        method_label.set_xalign(0)
        hbox.pack_start(method_label, True, True, 0)
        
        confidence_label = Gtk.Label()
        confidence_label.set_markup(f"<i>Confidence: {int(rec.confidence * 100)}%</i>")
        hbox.pack_start(confidence_label, False, False, 0)
        
        vbox.pack_start(hbox, False, False, 0)
        
        # Reasoning
        reasoning_label = Gtk.Label(label=rec.reasoning)
        reasoning_label.set_line_wrap(True)
        reasoning_label.set_xalign(0)
        vbox.pack_start(reasoning_label, False, False, 0)
        
        # Expected results
        results_hbox = Gtk.HBox(spacing=24)
        
        results_hbox.pack_start(
            self._create_info_label("Channels", str(rec.expected_results['channel_count'])),
            False, False, 0
        )
        results_hbox.pack_start(
            self._create_info_label("Quality", rec.expected_results['quality'].title()),
            False, False, 0
        )
        results_hbox.pack_start(
            self._create_info_label("Complexity", rec.expected_results['complexity'].replace('_', ' ').title()),
            False, False, 0
        )
        
        vbox.pack_start(results_hbox, False, False, 0)
        
        frame.add(vbox)
        return frame
    
    def create_methods_section(self):
        """Create method selection radio buttons"""
        frame = Gtk.Frame(label="Available Methods")
        frame.set_margin_top(6)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 300)
        
        vbox = Gtk.VBox(spacing=6)
        vbox.set_margin_left(12)
        vbox.set_margin_right(12)
        vbox.set_margin_top(6)
        vbox.set_margin_bottom(6)
        
        # Create radio buttons for all methods
        first_radio = None
        self.method_radios = {}
        
        for method in self.recommendations['all_methods']:
            radio = Gtk.RadioButton.new_with_label_from_widget(
                first_radio,
                method.method_name
            )
            if first_radio is None:
                first_radio = radio
            
            # Pre-select recommended method
            if method.method == self.recommendations['recommended'].method:
                radio.set_active(True)
            
            radio.connect('toggled', self.on_method_changed, method)
            self.method_radios[method.method] = radio
            
            # Method details
            details_box = Gtk.VBox(spacing=2)
            details_box.set_margin_left(32)
            
            # Score bar
            score_hbox = Gtk.HBox(spacing=6)
            score_label = Gtk.Label(label=f"Score: {int(method.score)}/100")
            score_hbox.pack_start(score_label, False, False, 0)
            
            score_bar = Gtk.ProgressBar()
            score_bar.set_fraction(method.score / 100)
            score_bar.set_show_text(False)
            score_hbox.pack_start(score_bar, True, True, 0)
            
            details_box.pack_start(score_hbox, False, False, 0)
            
            # Best for
            best_for_label = Gtk.Label()
            best_for_label.set_markup(f"<i>{method.best_for}</i>")
            best_for_label.set_line_wrap(True)
            best_for_label.set_xalign(0)
            details_box.pack_start(best_for_label, False, False, 0)
            
            vbox.pack_start(radio, False, False, 0)
            vbox.pack_start(details_box, False, False, 0)
            
            # Separator
            if method != self.recommendations['all_methods'][-1]:
                vbox.pack_start(Gtk.Separator(), False, False, 3)
        
        scrolled.add(vbox)
        frame.add(scrolled)
        return frame
    
    def create_parameters_section(self):
        """Create method-specific parameters"""
        frame = Gtk.Frame(label="Parameters")
        frame.set_margin_top(6)
        
        self.params_vbox = Gtk.VBox(spacing=6)
        self.params_vbox.set_margin_left(12)
        self.params_vbox.set_margin_right(12)
        self.params_vbox.set_margin_top(6)
        self.params_vbox.set_margin_bottom(6)
        
        # Initial parameters for recommended method
        self.update_parameters(self.recommendations['recommended'])
        
        frame.add(self.params_vbox)
        return frame
    
    def update_parameters(self, method):
        """Update parameter controls based on selected method"""
        # Clear existing
        for child in self.params_vbox.get_children():
            self.params_vbox.remove(child)
        
        # Add method-specific parameters
        if method.method == SeparationMethod.SPOT_COLOR:
            # Color tolerance
            hbox = Gtk.HBox(spacing=12)
            hbox.pack_start(Gtk.Label(label="Color Tolerance:"), False, False, 0)
            
            self.tolerance_adj = Gtk.Adjustment(value=10, lower=1, upper=30, step_increment=1)
            tolerance_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.tolerance_adj)
            tolerance_scale.set_hexpand(True)
            hbox.pack_start(tolerance_scale, True, True, 0)
            
            self.params_vbox.pack_start(hbox, False, False, 0)
        
        elif method.method == SeparationMethod.SIMULATED_PROCESS:
            # Halftone method
            hbox = Gtk.HBox(spacing=12)
            hbox.pack_start(Gtk.Label(label="Halftone Method:"), False, False, 0)

            self.halftone_combo = Gtk.ComboBoxText()
            self.halftone_combo.append_text("Stochastic")
            self.halftone_combo.append_text("Error Diffusion")
            self.halftone_combo.set_active(0)
            hbox.pack_start(self.halftone_combo, True, True, 0)

            self.params_vbox.pack_start(hbox, False, False, 0)

        elif method.method == SeparationMethod.INDEX_COLOR:
            # Dither method
            hbox = Gtk.HBox(spacing=12)
            hbox.pack_start(Gtk.Label(label="Dither Method:"), False, False, 0)

            self.dither_combo = Gtk.ComboBoxText()
            self.dither_combo.append_text("Floyd-Steinberg")
            self.dither_combo.append_text("None")
            self.dither_combo.set_active(0)
            hbox.pack_start(self.dither_combo, True, True, 0)

            self.params_vbox.pack_start(hbox, False, False, 0)

        self.params_vbox.show_all()
    
    def on_method_changed(self, radio, method):
        """Handle method selection change"""
        if radio.get_active():
            self.selected_method = method.method
            self.update_parameters(method)
    
    def get_selected_method(self):
        """Return selected separation method"""
        return self.selected_method
    
    def get_parameters(self):
        """Return method-specific parameters"""
        params = {}
        
        if self.selected_method == SeparationMethod.SPOT_COLOR:
            params['color_tolerance'] = self.tolerance_adj.get_value()
        elif self.selected_method == SeparationMethod.SIMULATED_PROCESS:
            params['halftone_method'] = self.halftone_combo.get_active_text().lower()
        elif self.selected_method == SeparationMethod.INDEX_COLOR:
            params['dither_method'] = self.dither_combo.get_active_text().lower().replace('-', '_')
        
        return params
    
    def _create_info_label(self, title, value):
        """Create info label pair"""
        vbox = Gtk.VBox(spacing=2)
        
        title_label = Gtk.Label()
        title_label.set_markup(f"<small><b>{title}</b></small>")
        vbox.pack_start(title_label, False, False, 0)
        
        value_label = Gtk.Label(label=value)
        vbox.pack_start(value_label, False, False, 0)
        
        return vbox
```

---

## Separation Coordinator

### Main Execution Logic

```python
"""
separation_coordinator.py - Routes to appropriate separation engine
"""

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('Gegl', '0.4')
from gi.repository import Gimp, Gegl, GLib
import numpy as np
from typing import Dict, List
import time

from separation.engines.spot_color_engine import SpotColorEngine
from separation.engines.simulated_process_engine import SimulatedProcessEngine
from separation.engines.index_color_engine import IndexColorEngine
from separation.engines.cmyk_engine import CMYKEngine
from separation.engines.rgb_engine import RGBEngine
from separation.engines.hybrid_ai_engine import HybridAIEngine

class SeparationCoordinator:
    """
    Coordinates separation execution
    Routes to appropriate engine and creates GIMP layers
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
        # Initialize engines
        self.engines = {
            SeparationMethod.SPOT_COLOR: SpotColorEngine(),
            SeparationMethod.SIMULATED_PROCESS: SimulatedProcessEngine(),
            SeparationMethod.INDEX_COLOR: IndexColorEngine(),
            SeparationMethod.CMYK: CMYKEngine(),
            SeparationMethod.RGB: RGBEngine(),
            SeparationMethod.HYBRID_AI: HybridAIEngine(api_key)
        }
    
    def execute_separation(
        self,
        image,
        drawable,
        method: SeparationMethod,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> bool:
        """
        Execute separation and create GIMP layers
        
        Args:
            image: GIMP image
            drawable: Source layer
            method: Selected separation method
            palette: Color palette from Color Match
            analysis_data: Analysis from Analyze unit
            parameters: Method-specific parameters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            start_time = time.time()
            
            # Get engine
            engine = self.engines[method]
            
            # Convert GIMP drawable to numpy
            rgb_array = self._drawable_to_numpy(drawable)
            
            # Execute separation
            Gimp.progress_init("Separating colors...")
            channels = engine.separate(
                rgb_array=rgb_array,
                palette=palette,
                analysis_data=analysis_data,
                parameters=parameters
            )
            
            # Create GIMP layers from channels
            Gimp.progress_init("Creating layers...")
            self._create_layers_from_channels(image, channels, palette)
            
            # Update display
            Gimp.displays_flush()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✓ Separation complete: {len(channels)} channels in {processing_time:.2f}s")
            return True
            
        except Exception as e:
            import traceback
            print(f"✗ Separation failed: {str(e)}")
            print(traceback.format_exc())
            return False
    
    def _drawable_to_numpy(self, drawable):
        """Convert GIMP drawable to numpy array"""
        width = drawable.get_width()
        height = drawable.get_height()
        
        # Get pixel buffer
        buffer = drawable.get_buffer()
        
        # Read pixel data
        rect = Gegl.Rectangle.new(0, 0, width, height)
        data = buffer.get(rect, 1.0, "R'G'B' u8", Gegl.AbyssPolicy.NONE)
        
        # Convert to numpy
        return np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
    
    def _create_layers_from_channels(
        self,
        image,
        channels: List[Dict],
        palette: List[Dict]
    ):
        """
        Create GIMP layers from separation channels
        
        Args:
            image: GIMP image
            channels: List of channel dictionaries with 'name' and 'data' keys
            palette: Color palette for layer colors
        """
        # Create layer group for separations
        layer_group = Gimp.LayerGroup.new(image)
        layer_group.set_name("Color Separations")
        image.insert_layer(layer_group, None, 0)
        
        # Create layer for each channel
        for idx, channel in enumerate(channels):
            layer = self._create_layer_from_channel(
                image,
                channel,
                palette[idx] if idx < len(palette) else None
            )
            
            # Add to group
            image.insert_layer(layer, layer_group, idx)
            
            # Update progress
            Gimp.progress_update((idx + 1) / len(channels))
        
        # Collapse group by default
        layer_group.set_expanded(False)
    
    def _create_layer_from_channel(
        self,
        image,
        channel: Dict,
        color_info: Dict = None
    ):
        """
        Create a single GIMP layer from channel data
        
        Args:
            image: GIMP image
            channel: Dictionary with 'name' and 'data' (numpy array)
            color_info: Optional color information from palette
            
        Returns:
            GIMP layer
        """
        channel_data = channel['data']
        height, width = channel_data.shape
        
        # Create new layer (grayscale)
        layer = Gimp.Layer.new(
            image,
            channel['name'],
            width,
            height,
            Gimp.ImageType.GRAY_IMAGE,
            100.0,  # opacity
            Gimp.LayerMode.NORMAL
        )
        
        # Get layer buffer
        buffer = layer.get_buffer()
        
        # Write channel data to buffer
        rect = Gegl.Rectangle.new(0, 0, width, height)
        buffer.set(
            rect,
            "Y' u8",
            channel_data.tobytes(),
            Gegl.AutoRowstride
        )
        
        # Flush buffer
        buffer.flush()
        
        # Set layer metadata
        if color_info:
            # Store color info as parasite
            import json
            color_parasite = Gimp.Parasite.new(
                "separation-color",
                Gimp.ParasiteFlags.PERSISTENT,
                json.dumps(color_info).encode('utf-8')
            )
            layer.attach_parasite(color_parasite)
        
        return layer
```

---

## Separation Engines

### Spot Color Engine

```python
"""
spot_color_engine.py - Spot color separation
Best for: 2-6 flat colors, sharp edges, logos
"""

import numpy as np
from typing import Dict, List
from scipy.spatial.distance import cdist

class SpotColorEngine:
    """
    Spot Color Separation
    Creates one channel per palette color using LAB color matching
    """
    
    def separate(
        self,
        rgb_array: np.ndarray,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> List[Dict]:
        """
        Execute spot color separation
        
        Args:
            rgb_array: Image as numpy array (H, W, 3)
            palette: List of color dictionaries
            analysis_data: Analysis results (unused for spot color)
            parameters: {'color_tolerance': float}
            
        Returns:
            List of channel dictionaries
        """
        tolerance = parameters.get('color_tolerance', 10.0)
        
        # Convert RGB to LAB
        lab_array = self._rgb_to_lab(rgb_array)
        
        channels = []
        
        for idx, color_info in enumerate(palette):
            # Extract channel for this specific color
            channel_data = self._extract_color_channel(
                lab_array,
                color_info['lab'],
                tolerance
            )
            
            channels.append({
                'name': color_info['name'],
                'data': channel_data,
                'color': color_info
            })
        
        return channels
    
    def _rgb_to_lab(self, rgb_array: np.ndarray) -> np.ndarray:
        """Convert RGB to LAB color space"""
        # Normalize RGB to 0-1
        rgb_normalized = rgb_array.astype(np.float32) / 255.0
        
        # RGB to XYZ (simplified D65 illuminant)
        xyz = np.zeros_like(rgb_normalized)
        xyz[:, :, 0] = 0.4124 * rgb_normalized[:, :, 0] + 0.3576 * rgb_normalized[:, :, 1] + 0.1805 * rgb_normalized[:, :, 2]
        xyz[:, :, 1] = 0.2126 * rgb_normalized[:, :, 0] + 0.7152 * rgb_normalized[:, :, 1] + 0.0722 * rgb_normalized[:, :, 2]
        xyz[:, :, 2] = 0.0193 * rgb_normalized[:, :, 0] + 0.1192 * rgb_normalized[:, :, 1] + 0.9505 * rgb_normalized[:, :, 2]
        
        # XYZ to LAB
        xyz_normalized = xyz / np.array([0.95047, 1.0, 1.08883])
        
        mask = xyz_normalized > 0.008856
        xyz_normalized[mask] = np.power(xyz_normalized[mask], 1/3)
        xyz_normalized[~mask] = 7.787 * xyz_normalized[~mask] + 16/116
        
        lab = np.zeros_like(xyz_normalized)
        lab[:, :, 0] = (116 * xyz_normalized[:, :, 1]) - 16  # L
        lab[:, :, 1] = 500 * (xyz_normalized[:, :, 0] - xyz_normalized[:, :, 1])  # a
        lab[:, :, 2] = 200 * (xyz_normalized[:, :, 1] - xyz_normalized[:, :, 2])  # b
        
        return lab
    
    def _extract_color_channel(
        self,
        lab_array: np.ndarray,
        target_lab: List[float],
        tolerance: float
    ) -> np.ndarray:
        """
        Extract channel for specific color using LAB distance
        
        Args:
            lab_array: Image in LAB space
            target_lab: Target color in LAB [L, a, b]
            tolerance: Delta-E tolerance
            
        Returns:
            Grayscale channel (0-255)
        """
        height, width = lab_array.shape[:2]
        channel_data = np.zeros((height, width), dtype=np.uint8)
        
        target_lab_array = np.array(target_lab)
        
        # Calculate Delta-E (Euclidean distance in LAB)
        delta_e = np.sqrt(np.sum((lab_array - target_lab_array) ** 2, axis=2))
        
        # Map to grayscale: closer match = brighter
        mask = delta_e <= tolerance
        channel_data[mask] = (255 * (1 - delta_e[mask] / tolerance)).astype(np.uint8)
        
        return channel_data
```

### Simulated Process Engine

```python
"""
simulated_process_engine.py - Simulated process separation
Best for: Photos, gradients, complex artwork
"""

import numpy as np
from typing import Dict, List

class SimulatedProcessEngine:
    """
    Simulated Process Separation
    Uses spectral decomposition for photorealistic results
    """
    
    def separate(
        self,
        rgb_array: np.ndarray,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> List[Dict]:
        """
        Execute simulated process separation
        
        Args:
            rgb_array: Image as numpy array
            palette: Color palette
            analysis_data: Analysis results
            parameters: {'halftone_method': str}
            
        Returns:
            List of channel dictionaries
        """
        halftone_method = parameters.get('halftone_method', 'stochastic')
        
        # Convert to LAB
        lab_array = self._rgb_to_lab(rgb_array)
        
        channels = []
        
        for idx, color_info in enumerate(palette):
            # Calculate ink contribution using spectral separation
            channel_data = self._spectral_separation(
                lab_array,
                color_info['lab'],
                [c['lab'] for c in palette]
            )
            
            # Apply halftoning/dithering
            if halftone_method == 'error_diffusion':
                channel_data = self._apply_error_diffusion(channel_data)
            
            channels.append({
                'name': color_info['name'],
                'data': channel_data,
                'color': color_info
            })
        
        return channels
    
    def _rgb_to_lab(self, rgb_array: np.ndarray) -> np.ndarray:
        """Convert RGB to LAB (reuse from SpotColorEngine)"""
        # Same implementation as SpotColorEngine
        rgb_normalized = rgb_array.astype(np.float32) / 255.0
        
        xyz = np.zeros_like(rgb_normalized)
        xyz[:, :, 0] = 0.4124 * rgb_normalized[:, :, 0] + 0.3576 * rgb_normalized[:, :, 1] + 0.1805 * rgb_normalized[:, :, 2]
        xyz[:, :, 1] = 0.2126 * rgb_normalized[:, :, 0] + 0.7152 * rgb_normalized[:, :, 1] + 0.0722 * rgb_normalized[:, :, 2]
        xyz[:, :, 2] = 0.0193 * rgb_normalized[:, :, 0] + 0.1192 * rgb_normalized[:, :, 1] + 0.9505 * rgb_normalized[:, :, 2]
        
        xyz_normalized = xyz / np.array([0.95047, 1.0, 1.08883])
        
        mask = xyz_normalized > 0.008856
        xyz_normalized[mask] = np.power(xyz_normalized[mask], 1/3)
        xyz_normalized[~mask] = 7.787 * xyz_normalized[~mask] + 16/116
        
        lab = np.zeros_like(xyz_normalized)
        lab[:, :, 0] = (116 * xyz_normalized[:, :, 1]) - 16
        lab[:, :, 1] = 500 * (xyz_normalized[:, :, 0] - xyz_normalized[:, :, 1])
        lab[:, :, 2] = 200 * (xyz_normalized[:, :, 1] - xyz_normalized[:, :, 2])
        
        return lab
    
    def _spectral_separation(
        self,
        lab_array: np.ndarray,
        target_ink_lab: List[float],
        all_inks_lab: List[List[float]]
    ) -> np.ndarray:
        """
        Calculate ink contribution using spectral decomposition
        Uses inverse distance weighting
        """
        height, width = lab_array.shape[:2]
        channel_data = np.zeros((height, width), dtype=np.uint8)
        
        target_lab = np.array(target_ink_lab)
        palette_lab = np.array(all_inks_lab)
        
        # Find target ink index
        target_idx = None
        for i, ink_lab in enumerate(all_inks_lab):
            if np.array_equal(ink_lab, target_ink_lab):
                target_idx = i
                break
        
        if target_idx is None:
            return channel_data
        
        # Calculate distances to all palette colors
        for y in range(height):
            for x in range(width):
                pixel_lab = lab_array[y, x]
                
                # Distance to each ink
                distances = np.sqrt(np.sum((palette_lab - pixel_lab) ** 2, axis=1))
                
                # Inverse distance weighting
                weights = 1.0 / (distances + 1e-6)
                weights_normalized = weights / np.sum(weights)
                
                # Contribution of target ink
                contribution = weights_normalized[target_idx]
                
                # Scale to 0-255
                channel_data[y, x] = int(contribution * 255)
        
        return channel_data
    
    def _apply_error_diffusion(self, channel_data: np.ndarray) -> np.ndarray:
        """Apply Floyd-Steinberg error diffusion dithering"""
        height, width = channel_data.shape
        dithered = channel_data.copy().astype(np.float32)
        
        for y in range(height):
            for x in range(width):
                old_val = dithered[y, x]
                new_val = 255 if old_val > 127 else 0
                dithered[y, x] = new_val
                
                error = old_val - new_val
                
                # Distribute error
                if x + 1 < width:
                    dithered[y, x + 1] += error * 7/16
                if y + 1 < height:
                    if x > 0:
                        dithered[y + 1, x - 1] += error * 3/16
                    dithered[y + 1, x] += error * 5/16
                    if x + 1 < width:
                        dithered[y + 1, x + 1] += error * 1/16
        
        return np.clip(dithered, 0, 255).astype(np.uint8)
```

### Index Color Engine

```python
"""
index_color_engine.py - Index color separation
Best for: 6-12 colors, balanced quality/cost
"""

import numpy as np
from typing import Dict, List

class IndexColorEngine:
    """
    Index Color Separation
    Quantizes image to palette colors with optional dithering
    """
    
    def separate(
        self,
        rgb_array: np.ndarray,
        palette: List[Dict],
        analysis_data: Dict,
        parameters: Dict
    ) -> List[Dict]:
        """
        Execute index color separation
        """
        dither_method = parameters.get('dither_method', 'floyd_steinberg')
        
        # Convert to LAB
        lab_array = self._rgb_to_lab(rgb_array)
        
        # Quantize to palette
        color_indices = self._quantize_to_palette(
            lab_array,
            [c['lab'] for c in palette],
            dither_method
        )
        
        # Create channel for each color
        channels = []
        
        for idx, color_info in enumerate(palette):
            # Extract pixels matching this color index
            mask = (color_indices == idx).astype(np.uint8) * 255
            
            channels.append({
                'name': color_info['name'],
                'data': mask,
                'color': color_info
            })
        
        return channels
    
    def _rgb_to_lab(self, rgb_array: np.ndarray) -> np.ndarray:
        """Convert RGB to LAB"""
        # Same as previous engines
        rgb_normalized = rgb_array.astype(np.float32) / 255.0
        
        xyz = np.zeros_like(rgb_normalized)
        xyz[:, :, 0] = 0.4124 * rgb_normalized[:, :, 0] + 0.3576 * rgb_normalized[:, :, 1] + 0.1805 * rgb_normalized[:, :, 2]
        xyz[:, :, 1] = 0.2126 * rgb_normalized[:, :, 0] + 0.7152 * rgb_normalized[:, :, 1] + 0.0722 * rgb_normalized[:, :, 2]
        xyz[:, :, 2] = 0.0193 * rgb_normalized[:, :, 0] + 0.1192 * rgb_normalized[:, :, 1] + 0.9505 * rgb_normalized[:, :, 2]
        
        xyz_normalized = xyz / np.array([0.95047, 1.0, 1.08883])
        
        mask = xyz_normalized > 0.008856
        xyz_normalized[mask] = np.power(xyz_normalized[mask], 1/3)
        xyz_normalized[~mask] = 7.787 * xyz_normalized[~mask] + 16/116
        
        lab = np.zeros_like(xyz_normalized)
        lab[:, :, 0] = (116 * xyz_normalized[:, :, 1]) - 16
        lab[:, :, 1] = 500 * (xyz_normalized[:, :, 0] - xyz_normalized[:, :, 1])
        lab[:, :, 2] = 200 * (xyz_normalized[:, :, 1] - xyz_normalized[:, :, 2])
        
        return lab
    
    def _quantize_to_palette(
        self,
        lab_array: np.ndarray,
        palette_lab: List[List[float]],
        dither_method: str
    ) -> np.ndarray:
        """
        Quantize image to palette colors
        
        Returns:
            Array of color indices
        """
        height, width = lab_array.shape[:2]
        color_indices = np.zeros((height, width), dtype=np.int32)
        
        palette_array = np.array(palette_lab)
        
        if dither_method == 'floyd_steinberg':
            # Floyd-Steinberg dithering
            lab_working = lab_array.copy().astype(np.float32)
            
            for y in range(height):
                for x in range(width):
                    old_pixel = lab_working[y, x]
                    
                    # Find closest palette color
                    distances = np.sqrt(np.sum((palette_array - old_pixel) ** 2, axis=1))
                    closest_idx = np.argmin(distances)
                    
                    new_pixel = palette_array[closest_idx]
                    color_indices[y, x] = closest_idx
                    lab_working[y, x] = new_pixel
                    
                    # Calculate and distribute error
                    error = old_pixel - new_pixel
                    
                    if x + 1 < width:
                        lab_working[y, x + 1] += error * 7/16
                    if y + 1 < height:
                        if x > 0:
                            lab_working[y + 1, x - 1] += error * 3/16
                        lab_working[y + 1, x] += error * 5/16
                        if x + 1 < width:
                            lab_working[y + 1, x + 1] += error * 1/16
        else:
            # No dithering - nearest neighbor
            for y in range(height):
                for x in range(width):
                    pixel_lab = lab_array[y, x]
                    distances = np.sqrt(np.sum((palette_array - pixel_lab) ** 2, axis=1))
                    color_indices[y, x] = np.argmin(distances)
        
        return color_indices
```

---

## Data Flow

```
GIMP Image
    ↓
User: Filters → AI Separation → Separate Colors (Step 3)
    ↓
Plugin checks for:
    - Analysis data (from Step 1)
    - Palette data (from Step 2)
    ↓
AI CALL #1: Method Analyzer
    - Analyze image + palette characteristics
    - Score all 6 methods
    - Return ranked recommendations
    ↓
Show GTK Dialog:
    - Display AI recommendation
    - Show all available methods with scores
    - Allow user selection/override
    - Show method-specific parameters
    ↓
User selects method and parameters
    ↓
Execute Separation:
    - Route to appropriate engine
    - Convert GIMP drawable → numpy
    - Run separation algorithm
    - Convert channels → numpy arrays
    ↓
Create GIMP Layers:
    - Create layer group "Color Separations"
    - For each channel:
        * Create grayscale layer
        * Write channel data
        * Set layer name
        * Store color metadata
    ↓
Complete:
    - Update GIMP display
    - Show success message
    - User adjusts with GIMP tools
```

---

## Testing Strategy

### Unit Tests

```python
def test_spot_color_separation():
    """Test spot color engine"""
    engine = SpotColorEngine()
    
    # Mock data
    test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    test_palette = [
        {'name': 'Red', 'rgb': [255, 0, 0], 'lab': [53.24, 80.09, 67.20]},
        {'name': 'Blue', 'rgb': [0, 0, 255], 'lab': [32.30, 79.19, -107.86]}
    ]
    
    channels = engine.separate(
        rgb_array=test_image,
        palette=test_palette,
        analysis_data={},
        parameters={'color_tolerance': 10.0}
    )
    
    assert len(channels) == 2
    assert channels[0]['name'] == 'Red'
    assert channels[0]['data'].shape == (100, 100)
```

### Integration Tests

```python
def test_full_separation_workflow():
    """Test complete separation workflow in GIMP"""
    # Run from GIMP Python console
    image = Gimp.image_list()[0]
    
    # Check parasites exist
    assert image.get_parasite("ai-separation-analysis")
    assert image.get_parasite("ai-separation-palette")
    
    # Run separation
    plugin = SeparationPlugin()
    # ... execute plugin
    
    # Check layers created
    layers = image.get_layers()
    assert any("Color Separations" in layer.get_name() for layer in layers)
```

---

## Performance Considerations

### Optimization Strategies

1. **Tile-based Processing** - For large images (>10MP)
2. **Numpy Vectorization** - Avoid Python loops where possible
3. **Progress Updates** - Keep UI responsive
4. **Lazy Loading** - Load engines on demand
5. **Caching** - Cache AI recommendations per image

### Memory Management

```python
def process_large_image(rgb_array, tile_size=512):
    """Process image in tiles to reduce memory usage"""
    height, width = rgb_array.shape[:2]
    
    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            tile = rgb_array[y:y+tile_size, x:x+tile_size]
            # Process tile
            yield process_tile(tile)
```

---

## Error Handling

```python
class SeparationError(Exception):
    """Base exception for separation errors"""
    pass

class MethodNotAvailableError(SeparationError):
    """Method requires features not available"""
    pass

class InsufficientDataError(SeparationError):
    """Missing required analysis or palette data"""
    pass

def handle_separation_error(error):
    """Show user-friendly error dialog"""
    dialog = Gtk.MessageDialog(
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text="Separation Error"
    )
    dialog.format_secondary_text(str(error))
    dialog.run()
    dialog.destroy()
```

---

## Summary

The Separation module completes the AI Color Separation plugin trilogy:

### Key Features
✅ **AI Method Recommendation** - Gemini analyzes image + palette  
✅ **6 Separation Methods** - Spot, Simulated, Index, CMYK, RGB, Hybrid  
✅ **User Selection** - Accept or override AI recommendation  
✅ **Direct Layer Creation** - Native GIMP layers ready for printing  
✅ **Method-Specific Parameters** - Tolerance, dithering, halftone options  
✅ **Progress Indication** - Responsive UI during processing  

### Code Reuse
- 80% of existing separation algorithms preserved
- Only UI and I/O layers rewritten for GIMP
- Total: ~3,000 lines (vs 4,500 standalone)

### Integration
- Seamless with Analyze and Color Match modules
- Uses GIMP's parasite system for data passing
- Native GTK dialogs matching GIMP UI
- Leverages GIMP's layer system

**Next Step:** Create Gemini API prompt for method recommendation (AI Call #1)

---

*End of Separation Module Specification v1.0-GIMP*