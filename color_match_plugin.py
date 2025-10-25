#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
color_match_plugin.py - GIMP AI Color Separation Plugin (Step 2: Color Match)

This plugin generates an optimal color palette for screen printing using AI.
It can extract colors from the image or use AI to recommend a palette.

Usage:
1. Run "Analyze Image (Step 1)" first
2. Run: Filters > AI Separation > Color Match (Step 2)
3. Select/confirm colors
4. Results stored for Step 3

Requirements:
- GIMP 3.0+
- Python 3.7+
- numpy
- google-generativeai (optional, for AI palette generation)
"""

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Gegl', '0.4')
from gi.repository import Gimp, Gtk, GObject, GLib, Gegl

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: NumPy not available. Some features will be limited.")

import json
import sys
import os
import time

# Add plugin directory to path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(plugin_dir, 'core'))

# Import color match modules
try:
    from color_match import GeminiPaletteGenerator, PaletteExtractor
    COLOR_MATCH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Color match modules not available: {e}")
    COLOR_MATCH_AVAILABLE = False

# Try to import color match dialog
try:
    sys.path.insert(0, os.path.join(plugin_dir, 'ui'))
    from color_match_dialog import ColorMatchDialog
    DIALOG_AVAILABLE = True
except ImportError:
    print("Warning: Color match dialog not available")
    DIALOG_AVAILABLE = False


class ColorMatchPlugin(Gimp.PlugIn):
    """
    GIMP plugin wrapper for AI Color Separation - Step 2: Color Match
    """

    def do_query_procedures(self):
        """Register procedures with GIMP"""
        return ['ai-separation-color-match']

    def do_create_procedure(self, name):
        """Create procedure definition"""
        procedure = Gimp.ImageProcedure.new(
            self, name,
            Gimp.PDBProcType.PLUGIN,
            self.run, None
        )

        procedure.set_image_types("*")
        procedure.set_menu_label("AI Separation: Color Match (Step 2)")
        procedure.add_menu_path('<Image>/Filters/Render')

        procedure.set_documentation(
            "Generate optimal color palette for screen printing",
            "Extracts or generates a color palette optimized for screen printing. "
            "Can use AI to recommend colors based on image analysis. "
            "This is Step 2 of the AI Color Separation workflow.",
            name
        )

        procedure.set_attribution(
            "AI Separation Team",
            "Copyright 2025",
            "2025"
        )

        return procedure

    def run(self, procedure, run_mode, image, n_drawables, drawables, config, data):
        """
        Execute color palette generation

        Workflow:
        1. Check for analysis data from Step 1
        2. Extract dominant colors from image
        3. Optionally use AI to optimize palette
        4. Show dialog for user to select/adjust colors
        5. Store palette as image parasite
        """
        try:
            # Check if color match modules available
            if not COLOR_MATCH_AVAILABLE:
                Gimp.message("Color match modules not found. Please check installation.")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.EXECUTION_ERROR,
                    GLib.Error("Color match modules not available")
                )

            # Check for analysis data from Step 1
            Gimp.progress_init("Checking prerequisites...")
            analysis_data = self._get_parasite_data(image, "ai-separation-analysis")

            if not analysis_data:
                Gimp.message("Analysis data not found.\n\nPlease run 'Analyze Image (Step 1)' first.")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error("Analysis data not found - run Step 1 first")
                )

            # Get drawable and convert to numpy
            drawable = drawables[0]
            Gimp.progress_init("Loading image data...")
            rgb_array = self._drawable_to_numpy(drawable)

            # Extract dominant colors
            Gimp.progress_init("Extracting colors...")
            Gimp.progress_update(0.3)

            extractor = PaletteExtractor()
            extracted_colors = extractor.extract_palette(
                rgb_array,
                max_colors=12,
                analysis_data=analysis_data
            )

            Gimp.progress_update(0.6)

            # Get Gemini API key (optional)
            api_key = self._get_api_key()

            # Optionally use AI to optimize palette
            if api_key:
                Gimp.progress_init("Optimizing palette with AI...")
                try:
                    generator = GeminiPaletteGenerator(api_key)
                    ai_palette = generator.generate_palette(
                        analysis_data=analysis_data,
                        target_count=len(extracted_colors),
                        extracted_colors=extracted_colors
                    )
                    # Use AI palette if successful
                    if ai_palette and 'colors' in ai_palette:
                        extracted_colors = ai_palette['colors']
                except Exception as e:
                    print(f"AI palette generation failed: {e}")
                    # Continue with extracted colors

            Gimp.progress_update(0.8)

            # Show dialog for user to confirm/adjust colors
            if DIALOG_AVAILABLE and run_mode == Gimp.RunMode.INTERACTIVE:
                palette_data = self._show_color_dialog(extracted_colors, analysis_data)

                if palette_data is None:
                    # User cancelled
                    return procedure.new_return_values(
                        Gimp.PDBStatusType.CANCEL,
                        GLib.Error("User cancelled")
                    )
            else:
                # Non-interactive or no dialog - use extracted colors
                palette_data = {
                    'colors': extracted_colors,
                    'color_count': len(extracted_colors),
                    'palette_type': 'extracted',
                    'timestamp': time.time()
                }

            # Store palette as parasite
            self._store_parasite(image, "ai-separation-palette", palette_data)

            Gimp.progress_update(1.0)

            # Show summary
            summary = self._create_summary_message(palette_data)
            Gimp.message(summary)

            return procedure.new_return_values(
                Gimp.PDBStatusType.SUCCESS,
                GLib.Error()
            )

        except Exception as e:
            import traceback
            error_msg = f"Color match failed:\n\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            Gimp.message(error_msg)
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(str(e))
            )

    def _get_parasite_data(self, image, parasite_name):
        """
        Retrieve JSON data from image parasite

        Args:
            image: GIMP image
            parasite_name: Name of parasite to retrieve

        Returns:
            Parsed JSON data or None if not found
        """
        try:
            parasite = image.get_parasite(parasite_name)
            if parasite:
                data = parasite.get_data().decode('utf-8')
                return json.loads(data)
        except Exception as e:
            print(f"Error reading parasite {parasite_name}: {e}")

        return None

    def _get_api_key(self):
        """
        Get Gemini API key from GIMP config directory

        Returns:
            API key string or None if not found
        """
        try:
            config_dir = os.path.join(
                GLib.get_user_config_dir(),
                'GIMP', '3.0', 'ai-separation'
            )
            key_file = os.path.join(config_dir, 'gemini_api.key')

            if os.path.exists(key_file):
                with open(key_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Error reading API key: {e}")

        return None

    def _drawable_to_numpy(self, drawable):
        """
        Convert GIMP drawable to numpy RGB array

        Args:
            drawable: GIMP drawable

        Returns:
            numpy array (H, W, 3) uint8 RGB
        """
        width = drawable.get_width()
        height = drawable.get_height()

        # Get pixel buffer
        buffer = drawable.get_buffer()

        # Read pixel data as RGB
        rect = Gegl.Rectangle.new(0, 0, width, height)
        data = buffer.get(rect, 1.0, "R'G'B' u8", Gegl.AbyssPolicy.NONE)

        # Convert to numpy
        return np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)

    def _show_color_dialog(self, colors, analysis_data):
        """
        Show dialog for user to select/adjust colors

        Args:
            colors: List of extracted colors
            analysis_data: Analysis from Step 1

        Returns:
            Palette data dict or None if cancelled
        """
        try:
            dialog = ColorMatchDialog(colors, analysis_data)
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                palette_data = dialog.get_palette_data()
                dialog.destroy()
                return palette_data
            else:
                dialog.destroy()
                return None

        except Exception as e:
            print(f"Dialog error: {e}")
            # Fallback: return colors without dialog
            return {
                'colors': colors,
                'color_count': len(colors),
                'palette_type': 'extracted',
                'timestamp': time.time()
            }

    def _store_parasite(self, image, parasite_name, data):
        """
        Store data as image parasite

        Args:
            image: GIMP image
            parasite_name: Name of parasite
            data: Data to store (will be JSON encoded)
        """
        json_data = json.dumps(data, indent=2)
        parasite = Gimp.Parasite.new(
            parasite_name,
            Gimp.ParasiteFlags.PERSISTENT,
            json_data.encode('utf-8')
        )
        image.attach_parasite(parasite)
        print(f"Stored parasite: {parasite_name} ({len(json_data)} bytes)")

    def _create_summary_message(self, palette_data):
        """
        Create user-friendly summary message

        Args:
            palette_data: Palette results dictionary

        Returns:
            Formatted summary string
        """
        colors = palette_data.get('colors', [])
        color_count = palette_data.get('color_count', len(colors))

        summary = "Color Palette Generated!\n\n"
        summary += "="*40 + "\n\n"

        summary += f"Colors in palette: {color_count}\n\n"

        # List colors
        summary += "PALETTE COLORS:\n"
        for i, color in enumerate(colors[:10], 1):  # Show first 10
            color_name = color.get('name', f'Color {i}')
            rgb = color.get('rgb', (0, 0, 0))
            hex_color = color.get('hex', self._rgb_to_hex(rgb))

            summary += f"  {i}. {color_name}: {hex_color}\n"

        if len(colors) > 10:
            summary += f"  ... and {len(colors) - 10} more\n"

        summary += "\n"
        summary += "="*40 + "\n"
        summary += "Next: Run 'Separate Colors (Step 3)'"

        return summary

    def _rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex string"""
        if isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
            return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"
        return "#000000"


# GIMP plugin entry point
Gimp.main(ColorMatchPlugin.__gtype__, sys.argv)
