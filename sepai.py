#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SepAI - AI-Powered Color Separation for GIMP
Copyright (C) 2025 SepAI Contributors
Licensed under GPL v3

Intelligent screen printing color separation using Google Gemini AI.
"""

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gegl', '4.0')

from gi.repository import Gimp, GimpUi, GObject, Gtk, Gdk, Gio, GLib, Gegl
import sys
import os
import json
import requests
from typing import List, Tuple, Dict, Optional
import tempfile
import base64
import numpy as np

# Import core analysis modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.analyze import AnalyzeUnitCoordinator, ColorAnalyzer
from core.data_structures import ProcessedImageData, ImageDimensions, AnalysisDataModel
from core.color_match import ColorMatchCoordinator

__version__ = '0.1.0'
__author__ = 'SepAI Contributors'
__license__ = 'GPL v3'

# Configuration file path
CONFIG_DIR = os.path.join(GLib.get_user_config_dir(), 'GIMP', '3.0', 'plug-ins', 'sepai')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

class Config:
    """Configuration manager for API keys and settings"""

    @staticmethod
    def ensure_config_dir():
        """Create config directory if it doesn't exist"""
        os.makedirs(CONFIG_DIR, exist_ok=True)

    @staticmethod
    def load():
        """Load configuration from file"""
        Config.ensure_config_dir()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    @staticmethod
    def save(config):
        """Save configuration to file"""
        Config.ensure_config_dir()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

    @staticmethod
    def get_api_key():
        """Get Gemini API key from config"""
        config = Config.load()
        return config.get('gemini_api_key', '')

    @staticmethod
    def set_api_key(api_key):
        """Save Gemini API key to config"""
        config = Config.load()
        config['gemini_api_key'] = api_key
        Config.save(config)


class GeminiAPI:
    """Interface to Google Gemini AI API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def analyze_image(self, image_data: bytes, prompt: str, model: str = "gemini-1.5-flash") -> Optional[str]:
        """
        Analyze image using Gemini Vision API

        Args:
            image_data: Image bytes (PNG format)
            prompt: Text prompt for analysis
            model: Gemini model to use

        Returns:
            Analysis text from Gemini or None on error
        """
        url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"

        # Convert image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_base64
                        }
                    }
                ]
            }]
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            return None

        except Exception as e:
            print(f"Gemini API error: {e}")
            return None


class GimpImageExtractor:
    """Extracts image data from GIMP for analysis"""

    @staticmethod
    def extract_image_data(image, drawable) -> ProcessedImageData:
        """
        Convert GIMP image/drawable to ProcessedImageData

        Args:
            image: GIMP image
            drawable: GIMP drawable (layer)

        Returns:
            ProcessedImageData ready for analysis
        """
        # Get dimensions
        width = drawable.get_width()
        height = drawable.get_height()

        # Get pixel buffer
        buffer = drawable.get_buffer()

        # Extract as numpy array
        rgb_array = GimpImageExtractor.buffer_to_numpy(buffer, width, height)

        # Convert RGB to LAB
        lab_array = ColorAnalyzer.rgb_to_lab(rgb_array)

        # Get image resolution
        res_x, res_y = image.get_resolution()

        # Create dimensions
        dimensions = ImageDimensions(
            original_width=width,
            original_height=height,
            original_dpi=res_x,
            working_width=min(width, 800),
            working_height=int(min(width, 800) * height / width)
        )

        # Create ProcessedImageData
        processed_data = ProcessedImageData(
            rgb_image=rgb_array,
            lab_image=lab_array,
            dimensions=dimensions,
            source_filename=image.get_name() or "untitled",
            source_filepath=image.get_file().get_path() if image.get_file() else ""
        )

        return processed_data

    @staticmethod
    def buffer_to_numpy(buffer, width: int, height: int) -> np.ndarray:
        """Convert GIMP GeglBuffer to numpy array"""
        try:
            # Get format info
            format_str = buffer.get_format()

            # Try to get format as Babl format
            if hasattr(Gegl, 'babl_format'):
                fmt = Gegl.babl_format("R'G'B' u8")
            else:
                fmt = format_str

            # Read pixel data
            rect = Gegl.Rectangle()
            rect.x = 0
            rect.y = 0
            rect.width = width
            rect.height = height

            # Allocate buffer for RGB data
            pixel_data = bytearray(width * height * 3)

            # Get the pixels
            buffer.get(rect, 1.0, fmt, pixel_data, Gegl.AUTO_ROWSTRIDE)

            # Convert to numpy array
            rgb_array = np.frombuffer(pixel_data, dtype=np.uint8).reshape(height, width, 3)

            return rgb_array.copy()

        except Exception as e:
            print(f"Error extracting buffer: {e}")
            # Fallback: create a simple array
            return np.zeros((height, width, 3), dtype=np.uint8)


class ImageAnalyzer:
    """Analyzes images for color separation using AI"""

    @staticmethod
    def export_image_as_png(image) -> bytes:
        """Export GIMP image as PNG bytes"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        try:
            # Export image
            layer = image.get_active_layer()
            file = Gio.file_new_for_path(temp_path)
            Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, [layer], file)

            # Read the file
            with open(temp_path, 'rb') as f:
                data = f.read()

            return data
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @staticmethod
    def analyze_colors(image, drawable, api_key: str) -> Optional[Dict]:
        """
        Comprehensive image analysis combining local analysis and Gemini AI

        Returns dict with:
        - local_analysis: Results from local image analysis
        - ai_analysis: Results from Gemini AI
        - combined_recommendations: Merged recommendations
        """
        results = {}

        # Perform local image analysis first
        try:
            extractor = GimpImageExtractor()
            processed_data = extractor.extract_image_data(image, drawable)

            analyzer = AnalyzeUnitCoordinator()
            local_analysis = analyzer.process(processed_data)

            results['local_analysis'] = local_analysis.to_dict()
        except Exception as e:
            print(f"Local analysis error: {e}")
            results['local_analysis'] = None

        # Perform Gemini AI analysis
        if api_key:
            try:
                gemini = GeminiAPI(api_key)
                image_data = ImageAnalyzer.export_image_as_png(image)

                prompt = """Analyze this image for screen printing color separation. Provide:

1. DOMINANT COLORS: List the 3-8 most prominent colors (as RGB values or color names)
2. RECOMMENDED COLOR COUNT: How many spot colors would work best (2-8 colors)
3. SEPARATION METHOD: Best approach (Spot Color, CMYK, Simulated Process, or Index)
4. IMAGE CHARACTERISTICS: Note complexity, gradients, fine details, edge sharpness
5. RECOMMENDATIONS: Specific advice for optimal separation

Format your response as JSON:
{
  "dominant_colors": ["color1", "color2", ...],
  "color_count": 4,
  "separation_method": "Spot Color",
  "characteristics": "description",
  "recommendations": "advice"
}"""

                response = gemini.analyze_image(image_data, prompt)

                if response:
                    try:
                        json_start = response.find('{')
                        json_end = response.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = response[json_start:json_end]
                            results['ai_analysis'] = json.loads(json_str)
                        else:
                            results['ai_analysis'] = {'raw_response': response}
                    except:
                        results['ai_analysis'] = {'raw_response': response}
                else:
                    results['ai_analysis'] = None
            except Exception as e:
                print(f"AI analysis error: {e}")
                results['ai_analysis'] = None
        else:
            results['ai_analysis'] = None

        # Combine recommendations
        ImageAnalyzer._combine_recommendations(results)

        return results

    @staticmethod
    def _combine_recommendations(results: Dict):
        """Combine local and AI analysis into unified recommendations"""
        local = results.get('local_analysis')
        ai = results.get('ai_analysis')

        combined = {}

        # Prefer local analysis for color count if available
        if local and 'color_analysis' in local:
            combined['color_count'] = local['color_analysis']['color_count_estimate']
            combined['complexity'] = local['color_analysis']['color_complexity']
            combined['has_gradients'] = local['color_analysis']['has_gradients']
            combined['recommended_method'] = local['color_analysis']['recommended_method']

        # Override with AI if available and different
        if ai and isinstance(ai, dict) and 'color_count' in ai:
            # Average the two recommendations
            if 'color_count' in combined:
                combined['color_count'] = round((combined['color_count'] + ai['color_count']) / 2)
            else:
                combined['color_count'] = ai['color_count']

            # Prefer AI method recommendation
            if 'separation_method' in ai:
                combined['ai_method'] = ai['separation_method']

        # Add edge and texture info from local analysis
        if local:
            if 'edge_analysis' in local:
                combined['edge_density'] = local['edge_analysis']['edge_density']
                combined['detail_level'] = local['edge_analysis']['detail_level']
            if 'texture_analysis' in local:
                combined['texture_complexity'] = local['texture_analysis']['texture_complexity']

        results['combined_recommendations'] = combined


class ColorSeparator:
    """Performs color separation operations"""

    @staticmethod
    def separate_by_index(image, num_colors: int):
        """Convert image to indexed mode with specified number of colors"""
        # Flatten image first
        if image.get_base_type() != Gimp.ImageBaseType.INDEXED:
            # Convert to indexed
            Gimp.Image.convert_indexed(
                image,
                Gimp.ConvertDitherType.NONE,
                Gimp.ConvertPaletteType.GENERATE,
                num_colors,
                False,
                False,
                ""
            )

    @staticmethod
    def create_spot_color_layers(image, colors: List[str], api_key: str) -> List:
        """
        Create separate layers for each spot color
        Uses AI to identify which pixels belong to each color
        """
        layers = []
        width = image.get_width()
        height = image.get_height()

        # Get the active layer
        source_layer = image.get_active_layer()

        for i, color_name in enumerate(colors):
            # Create new layer for this color
            layer = Gimp.Layer.new(
                image,
                f"Spot Color {i+1}: {color_name}",
                width,
                height,
                Gimp.ImageType.RGBA_IMAGE,
                100.0,
                Gimp.LayerMode.NORMAL
            )

            image.insert_layer(layer, None, 0)
            layers.append(layer)

        return layers

    @staticmethod
    def separate_cmyk(image):
        """Separate image into CMYK channels"""
        Gimp.Image.convert_color_profile(
            image,
            Gimp.get_color_configuration().get_cmyk_color_profile()
        )

        # Decompose to CMYK
        new_image = Gimp.Image.decompose(
            image,
            "CMYK",
            Gimp.RunMode.NONINTERACTIVE
        )

        return new_image


class SepAIDialog:
    """Main dialog for SepAI plugin"""

    def __init__(self, image, drawable):
        self.image = image
        self.drawable = drawable
        self.api_key = Config.get_api_key()
        self.analysis_result = None
        self.analysis_data_model = None
        self.color_match_coordinator = None
        self.generated_palette = None

        self.dialog = GimpUi.Dialog(
            title="SepAI - AI Color Separation",
            role="sepai-dialog",
            use_header_bar=True
        )

        self.dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.dialog.add_button("_Separate", Gtk.ResponseType.OK)

        self.build_ui()

    def build_ui(self):
        """Build the dialog UI"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # API Key section
        if not self.api_key:
            api_frame = Gtk.Frame(label="Gemini API Key Required")
            api_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            api_box.set_margin_start(6)
            api_box.set_margin_end(6)
            api_box.set_margin_top(6)
            api_box.set_margin_bottom(6)

            label = Gtk.Label(label="Get your free API key from:")
            api_box.pack_start(label, False, False, 0)

            link = Gtk.LinkButton(
                uri="https://aistudio.google.com/app/apikey",
                label="Google AI Studio"
            )
            api_box.pack_start(link, False, False, 0)

            api_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            self.api_entry = Gtk.Entry()
            self.api_entry.set_placeholder_text("Enter API Key")
            self.api_entry.set_visibility(False)
            api_entry_box.pack_start(self.api_entry, True, True, 0)

            save_btn = Gtk.Button(label="Save")
            save_btn.connect("clicked", self.on_save_api_key)
            api_entry_box.pack_start(save_btn, False, False, 0)

            api_box.pack_start(api_entry_box, False, False, 0)
            api_frame.add(api_box)
            box.pack_start(api_frame, False, False, 0)

        # Analysis section
        analyze_frame = Gtk.Frame(label="AI Image Analysis")
        analyze_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        analyze_box.set_margin_start(6)
        analyze_box.set_margin_end(6)
        analyze_box.set_margin_top(6)
        analyze_box.set_margin_bottom(6)

        analyze_btn = Gtk.Button(label="Analyze Image with AI")
        analyze_btn.connect("clicked", self.on_analyze)
        analyze_box.pack_start(analyze_btn, False, False, 0)

        # Results text view
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(150)
        self.results_view = Gtk.TextView()
        self.results_view.set_editable(False)
        self.results_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scroll.add(self.results_view)
        analyze_box.pack_start(scroll, True, True, 0)

        analyze_frame.add(analyze_box)
        box.pack_start(analyze_frame, True, True, 0)

        # Color Match section
        palette_frame = Gtk.Frame(label="Color Palette Generation")
        palette_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        palette_box.set_margin_start(6)
        palette_box.set_margin_end(6)
        palette_box.set_margin_top(6)
        palette_box.set_margin_bottom(6)

        # Generate palette button
        palette_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.generate_palette_btn = Gtk.Button(label="Generate Palette with AI")
        self.generate_palette_btn.connect("clicked", self.on_generate_palette)
        self.generate_palette_btn.set_sensitive(False)  # Enabled after analysis
        palette_btn_box.pack_start(self.generate_palette_btn, True, True, 0)
        palette_box.pack_start(palette_btn_box, False, False, 0)

        # Palette display area
        palette_scroll = Gtk.ScrolledWindow()
        palette_scroll.set_min_content_height(100)
        self.palette_view = Gtk.TextView()
        self.palette_view.set_editable(False)
        self.palette_view.set_wrap_mode(Gtk.WrapMode.WORD)
        palette_scroll.add(self.palette_view)
        palette_box.pack_start(palette_scroll, True, True, 0)

        palette_frame.add(palette_box)
        box.pack_start(palette_frame, True, True, 0)

        # Separation settings
        sep_frame = Gtk.Frame(label="Separation Settings")
        sep_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sep_box.set_margin_start(6)
        sep_box.set_margin_end(6)
        sep_box.set_margin_top(6)
        sep_box.set_margin_bottom(6)

        # Method selection
        method_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        method_box.pack_start(Gtk.Label(label="Method:"), False, False, 0)

        self.method_combo = Gtk.ComboBoxText()
        self.method_combo.append_text("Spot Color (Index)")
        self.method_combo.append_text("CMYK")
        self.method_combo.append_text("Simulated Process")
        self.method_combo.append_text("Index Color")
        self.method_combo.set_active(0)
        method_box.pack_start(self.method_combo, True, True, 0)
        sep_box.pack_start(method_box, False, False, 0)

        # Number of colors
        colors_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        colors_box.pack_start(Gtk.Label(label="Number of Colors:"), False, False, 0)

        self.colors_spin = Gtk.SpinButton()
        self.colors_spin.set_range(2, 12)
        self.colors_spin.set_increments(1, 1)
        self.colors_spin.set_value(4)
        colors_box.pack_start(self.colors_spin, False, False, 0)
        sep_box.pack_start(colors_box, False, False, 0)

        sep_frame.add(sep_box)
        box.pack_start(sep_frame, False, False, 0)

        # Add to dialog
        content_area = self.dialog.get_content_area()
        content_area.add(box)
        self.dialog.set_default_size(500, 600)

    def on_save_api_key(self, button):
        """Save API key to config"""
        api_key = self.api_entry.get_text().strip()
        if api_key:
            Config.set_api_key(api_key)
            self.api_key = api_key

            # Show success message
            dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="API Key Saved"
            )
            dialog.format_secondary_text("Your Gemini API key has been saved successfully.")
            dialog.run()
            dialog.destroy()

    def on_analyze(self, button):
        """Run AI analysis on image"""
        if not self.api_key:
            dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="API Key Required"
            )
            dialog.format_secondary_text("Please enter and save your Gemini API key first.")
            dialog.run()
            dialog.destroy()
            return

        # Show progress
        button.set_sensitive(False)
        buffer = self.results_view.get_buffer()
        buffer.set_text("Analyzing image with Gemini AI...\n\nThis may take a few seconds...")

        # Run analysis in background
        GLib.idle_add(self.do_analyze, button)

    def do_analyze(self, button):
        """Perform the actual analysis"""
        try:
            # Get active drawable
            drawable = self.drawable if self.drawable else self.image.get_active_layer()

            # Run comprehensive analysis
            self.analysis_result = ImageAnalyzer.analyze_colors(self.image, drawable, self.api_key)

            if self.analysis_result:
                # Format results combining local and AI analysis
                buffer = self.results_view.get_buffer()
                text = self._format_analysis_results(self.analysis_result)
                buffer.set_text(text)

                # Save AnalysisDataModel for palette generation
                local_analysis = self.analysis_result.get('local_analysis')
                if local_analysis:
                    try:
                        self.analysis_data_model = AnalysisDataModel.from_dict(local_analysis)
                        # Enable palette generation button
                        self.generate_palette_btn.set_sensitive(True)
                    except Exception as e:
                        print(f"Error creating AnalysisDataModel: {e}")

                # Update UI with combined recommendations
                combined = self.analysis_result.get('combined_recommendations', {})

                if 'color_count' in combined:
                    self.colors_spin.set_value(combined['color_count'])

                if 'recommended_method' in combined:
                    method = combined['recommended_method']
                    if method == 'cmyk':
                        self.method_combo.set_active(1)
                    elif method == 'simulated_process':
                        self.method_combo.set_active(2)
                    elif method == 'index':
                        self.method_combo.set_active(3)
                    else:  # spot_color
                        self.method_combo.set_active(0)
            else:
                buffer = self.results_view.get_buffer()
                buffer.set_text("Analysis failed. Please check your settings and try again.")

        except Exception as e:
            import traceback
            buffer = self.results_view.get_buffer()
            error_text = f"Error during analysis:\n{str(e)}\n\n{traceback.format_exc()}"
            buffer.set_text(error_text)
            print(error_text)

        button.set_sensitive(True)
        return False

    def _format_analysis_results(self, results: Dict) -> str:
        """Format analysis results for display"""
        text = "=== IMAGE ANALYSIS RESULTS ===\n\n"

        # Combined recommendations section
        combined = results.get('combined_recommendations', {})
        if combined:
            text += "RECOMMENDATIONS:\n"
            text += f"  Color Count: {combined.get('color_count', 'N/A')}\n"
            text += f"  Method: {combined.get('recommended_method', 'N/A')}\n"
            text += f"  Complexity: {combined.get('complexity', 0):.2f}\n"
            text += f"  Detail Level: {combined.get('detail_level', 'N/A')}\n"

            if combined.get('has_gradients'):
                text += "  ⚠ Image contains gradients\n"

            text += "\n"

        # Local analysis section
        local = results.get('local_analysis')
        if local:
            text += "LOCAL ANALYSIS:\n"

            # Color info
            if 'color_analysis' in local:
                color = local['color_analysis']
                text += f"  Dominant Colors: {len(color.get('clusters', []))}\n"
                text += f"  Unique Colors: {color.get('unique_color_count', 0)}\n"

                # Show top colors
                clusters = color.get('clusters', [])
                if clusters:
                    text += "  Top Colors:\n"
                    for i, cluster in enumerate(clusters[:5]):
                        rgb = cluster['center_rgb']
                        pct = cluster['percentage']
                        text += f"    {i+1}. RGB{rgb} ({pct:.1f}%)\n"

            # Edge info
            if 'edge_analysis' in local:
                edge = local['edge_analysis']
                text += f"  Edge Density: {edge.get('edge_density', 0):.2f}\n"
                text += f"  Edge Sharpness: {edge.get('edge_sharpness', 0):.2f}\n"
                if edge.get('has_fine_lines'):
                    text += "  ⚠ Contains fine lines\n"
                if edge.get('has_halftones'):
                    text += "  ⚠ Contains halftones\n"

            # Texture info
            if 'texture_analysis' in local:
                texture = local['texture_analysis']
                text += f"  Texture: {texture.get('grain_size', 'none')}\n"
                patterns = texture.get('dominant_patterns', [])
                if patterns:
                    text += f"  Patterns: {', '.join(patterns)}\n"

            text += "\n"

        # AI analysis section
        ai = results.get('ai_analysis')
        if ai and isinstance(ai, dict):
            text += "AI ANALYSIS (Gemini):\n"

            if 'raw_response' in ai:
                text += ai['raw_response']
            else:
                text += f"  Recommended Colors: {ai.get('color_count', 'N/A')}\n"
                text += f"  Method: {ai.get('separation_method', 'N/A')}\n\n"

                if 'dominant_colors' in ai:
                    text += "  Dominant Colors:\n"
                    for color in ai.get('dominant_colors', []):
                        text += f"    - {color}\n"

                if 'characteristics' in ai:
                    text += f"\n  Characteristics:\n  {ai['characteristics']}\n\n"

                if 'recommendations' in ai:
                    text += f"  AI Recommendations:\n  {ai['recommendations']}\n"

        elif ai is None and self.api_key:
            text += "\n(AI analysis unavailable)\n"

        return text

    def on_generate_palette(self, button):
        """Generate color palette with AI"""
        if not self.api_key:
            dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="API Key Required"
            )
            dialog.format_secondary_text("Please enter and save your Gemini API key first.")
            dialog.run()
            dialog.destroy()
            return

        if not self.analysis_data_model:
            dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Analysis Required"
            )
            dialog.format_secondary_text("Please run image analysis first.")
            dialog.run()
            dialog.destroy()
            return

        # Show progress
        button.set_sensitive(False)
        button.set_label("Generating Palette...")
        buffer = self.palette_view.get_buffer()
        buffer.set_text("Generating palette with Gemini AI...\n\nThis may take a few seconds...")

        # Run generation in background
        GLib.idle_add(self.do_generate_palette, button)

    def do_generate_palette(self, button):
        """Perform the actual palette generation"""
        try:
            # Get target color count
            target_count = int(self.colors_spin.get_value())

            # Initialize coordinator if needed
            if not self.color_match_coordinator:
                self.color_match_coordinator = ColorMatchCoordinator(self.api_key)

            # Set analysis data
            self.color_match_coordinator.set_analysis_data(self.analysis_data_model)

            # Generate palette with AI
            result = self.color_match_coordinator.generate_palette_with_ai(target_count)

            if result.get('error'):
                # Show error
                buffer = self.palette_view.get_buffer()
                buffer.set_text(f"Palette generation failed:\n{result.get('message', 'Unknown error')}")
            else:
                # Success! Display palette
                self.generated_palette = result
                buffer = self.palette_view.get_buffer()
                text = self._format_palette_results(result)
                buffer.set_text(text)

                # Update color count if different from target
                actual_count = len(result.get('palette', []))
                if actual_count != target_count:
                    self.colors_spin.set_value(actual_count)

        except Exception as e:
            import traceback
            buffer = self.palette_view.get_buffer()
            error_text = f"Error during palette generation:\n{str(e)}\n\n{traceback.format_exc()}"
            buffer.set_text(error_text)
            print(error_text)

        # Reset button
        button.set_sensitive(True)
        button.set_label("Generate Palette with AI")
        return False

    def _format_palette_results(self, result: Dict) -> str:
        """Format palette results for display"""
        text = "=== AI PALETTE RECOMMENDATION ===\n\n"

        # Strategy
        strategy = result.get('overall_strategy', '')
        if strategy:
            text += f"STRATEGY:\n{strategy}\n\n"

        # Palette
        palette = result.get('palette', [])
        if palette:
            text += f"PALETTE ({len(palette)} colors):\n\n"
            for i, color in enumerate(palette, 1):
                rgb = color.get('rgb', [0, 0, 0])
                name = color.get('name', f'Color {i}')
                pantone = color.get('pantone_match', 'None')
                angle = color.get('halftone_angle', 45)
                lpi = color.get('suggested_frequency', 55)
                coverage = color.get('coverage_estimate', 0.0)
                reasoning = color.get('reasoning', '')

                text += f"{i}. {name}\n"
                text += f"   RGB: ({rgb[0]}, {rgb[1]}, {rgb[2]})\n"
                text += f"   Pantone: {pantone}\n"
                text += f"   Halftone: {angle}° @ {lpi} LPI\n"
                text += f"   Coverage: {coverage*100:.1f}%\n"
                if reasoning:
                    text += f"   Note: {reasoning}\n"
                text += "\n"

        # CMYK alternative
        cmyk_alt = result.get('cmyk_alternative')
        if cmyk_alt:
            text += "CMYK ALTERNATIVE:\n"
            text += f"  Feasible: {cmyk_alt.get('feasible', False)}\n"
            text += f"  {cmyk_alt.get('reasoning', '')}\n\n"

        # Production notes
        notes = result.get('production_notes', [])
        if notes:
            text += "PRODUCTION NOTES:\n"
            for note in notes:
                text += f"  • {note}\n"
            text += "\n"

        # Confidence and warnings
        confidence = result.get('confidence_score', 0.0)
        text += f"Confidence: {confidence*100:.0f}%\n"

        warnings = result.get('validation_warnings', [])
        if warnings:
            text += "\nWARNINGS:\n"
            for warning in warnings:
                text += f"  ⚠ {warning}\n"

        return text

    def run(self):
        """Show dialog and return response"""
        self.dialog.show_all()
        response = self.dialog.run()

        result = None
        if response == Gtk.ResponseType.OK:
            result = {
                'method': self.method_combo.get_active(),
                'num_colors': int(self.colors_spin.get_value()),
                'analysis': self.analysis_result
            }

        self.dialog.destroy()
        return result


class SepAI(Gimp.PlugIn):
    """Main plugin class"""

    ## GimpPlugIn virtual methods ##
    def do_query_procedures(self):
        return ['sepai-color-separation']

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name,
            Gimp.PDBProcType.PLUGIN,
            self.run, None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_menu_label("SepAI Color Separation...")
        procedure.add_menu_path('<Image>/Filters/SepAI/')

        procedure.set_documentation(
            "AI-powered color separation for screen printing",
            "Uses Google Gemini AI to analyze images and create intelligent color separations optimized for screen printing. Supports spot color, CMYK, and simulated process separations.",
            name
        )

        procedure.set_attribution(__author__, __author__, "2025")

        return procedure

    def run(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Main plugin execution"""

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("sepai.py")

            drawable = drawables[0] if n_drawables > 0 else None

            # Show main dialog
            dialog = SepAIDialog(image, drawable)
            result = dialog.run()

            if result:
                # Perform separation based on settings
                Gimp.context_push()
                image.undo_group_start()

                try:
                    method = result['method']
                    num_colors = result['num_colors']

                    if method == 0:  # Spot Color (Index)
                        ColorSeparator.separate_by_index(image, num_colors)
                    elif method == 1:  # CMYK
                        ColorSeparator.separate_cmyk(image)
                    elif method == 3:  # Index Color
                        ColorSeparator.separate_by_index(image, num_colors)

                    Gimp.displays_flush()

                except Exception as e:
                    Gimp.message(f"Separation error: {str(e)}")

                finally:
                    image.undo_group_end()
                    Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(SepAI.__gtype__, sys.argv)
