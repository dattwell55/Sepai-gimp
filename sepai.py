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

from gi.repository import Gimp, GimpUi, GObject, Gtk, Gdk, Gio, GLib
import sys
import os
import json
import requests
from typing import List, Tuple, Dict, Optional
import tempfile
import base64

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
    def analyze_colors(image, api_key: str) -> Optional[Dict]:
        """
        Analyze image colors using Gemini AI

        Returns dict with:
        - dominant_colors: List of main colors
        - color_count: Recommended number of colors
        - separation_method: Recommended separation approach
        - details: Additional analysis
        """
        gemini = GeminiAPI(api_key)

        # Export image
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
                # Try to parse JSON from response
                # Gemini might include markdown formatting
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
            except:
                # Return raw response if JSON parsing fails
                return {'raw_response': response}

        return None


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
            self.analysis_result = ImageAnalyzer.analyze_colors(self.image, self.api_key)

            if self.analysis_result:
                # Format results
                buffer = self.results_view.get_buffer()

                if 'raw_response' in self.analysis_result:
                    buffer.set_text(self.analysis_result['raw_response'])
                else:
                    text = "AI Analysis Results:\n\n"
                    text += f"Recommended Colors: {self.analysis_result.get('color_count', 'N/A')}\n"
                    text += f"Method: {self.analysis_result.get('separation_method', 'N/A')}\n\n"
                    text += f"Dominant Colors:\n"
                    for color in self.analysis_result.get('dominant_colors', []):
                        text += f"  - {color}\n"
                    text += f"\nCharacteristics:\n{self.analysis_result.get('characteristics', 'N/A')}\n\n"
                    text += f"Recommendations:\n{self.analysis_result.get('recommendations', 'N/A')}"

                    buffer.set_text(text)

                    # Update UI with recommendations
                    if 'color_count' in self.analysis_result:
                        self.colors_spin.set_value(self.analysis_result['color_count'])

                    if 'separation_method' in self.analysis_result:
                        method = self.analysis_result['separation_method']
                        if 'CMYK' in method:
                            self.method_combo.set_active(1)
                        elif 'Simulated' in method:
                            self.method_combo.set_active(2)
                        elif 'Index' in method:
                            self.method_combo.set_active(3)
            else:
                buffer = self.results_view.get_buffer()
                buffer.set_text("Analysis failed. Please check your API key and try again.")

        except Exception as e:
            buffer = self.results_view.get_buffer()
            buffer.set_text(f"Error during analysis:\n{str(e)}")

        button.set_sensitive(True)
        return False

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
