#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_plugin.py - GIMP AI Color Separation Plugin (Step 1: Analyze Image)

This plugin performs comprehensive image analysis for color separation optimization.
It analyzes colors, edges, gradients, and texture to inform the separation process.

Usage:
1. Open an image in GIMP
2. Run: Filters > AI Separation > Analyze Image (Step 1)
3. Results stored as image parasite for Step 2

Requirements:
- GIMP 3.0+
- Python 3.7+
- numpy
- scipy (optional, for advanced features)
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

# Import analysis modules
try:
    from analyze import ColorAnalyzer, EdgeAnalyzer, TextureAnalyzer
    from data_structures import AnalysisDataModel
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Analysis modules not available: {e}")
    ANALYSIS_AVAILABLE = False


class AnalyzePlugin(Gimp.PlugIn):
    """
    GIMP plugin wrapper for AI Color Separation - Step 1: Analyze Image
    """

    def do_query_procedures(self):
        """Register procedures with GIMP"""
        return ['ai-separation-analyze']

    def do_create_procedure(self, name):
        """Create procedure definition"""
        procedure = Gimp.ImageProcedure.new(
            self, name,
            Gimp.PDBProcType.PLUGIN,
            self.run, None
        )

        procedure.set_image_types("*")
        procedure.set_menu_label("AI Separation: Analyze Image (Step 1)")
        procedure.add_menu_path('<Image>/Filters/Render')

        procedure.set_documentation(
            "Analyze image for AI-powered color separation",
            "Performs comprehensive analysis of colors, edges, gradients, and texture. "
            "This is Step 1 of the AI Color Separation workflow. "
            "Results are stored for use in Steps 2 and 3.",
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
        Execute image analysis

        Workflow:
        1. Convert GIMP drawable to numpy array
        2. Perform comprehensive analysis:
           - Color analysis (unique colors, gradients, complexity)
           - Edge analysis (sharp vs soft, line work detection)
           - Texture analysis (photo vs vector detection)
        3. Store results as image parasite
        """
        try:
            # Check if analysis modules available
            if not ANALYSIS_AVAILABLE:
                Gimp.message("Analysis modules not found. Please check installation.")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.EXECUTION_ERROR,
                    GLib.Error("Analysis modules not available")
                )

            # Get drawable
            drawable = drawables[0]

            # Convert to numpy array
            Gimp.progress_init("Loading image data...")
            rgb_array = self._drawable_to_numpy(drawable)

            image_width = drawable.get_width()
            image_height = drawable.get_height()

            print(f"Analyzing image: {image_width}x{image_height}")

            # Perform color analysis
            Gimp.progress_init("Analyzing colors...")
            Gimp.progress_update(0.2)

            color_analyzer = ColorAnalyzer()
            color_analysis = color_analyzer.analyze(rgb_array)

            # Perform edge analysis
            Gimp.progress_init("Analyzing edges...")
            Gimp.progress_update(0.5)

            edge_analyzer = EdgeAnalyzer()
            edge_analysis = edge_analyzer.analyze(rgb_array)

            # Perform texture analysis
            Gimp.progress_init("Analyzing texture...")
            Gimp.progress_update(0.8)

            texture_analyzer = TextureAnalyzer()
            texture_analysis = texture_analyzer.analyze(rgb_array)

            # Build analysis data model
            analysis_data = {
                'image_dimensions': {
                    'width': image_width,
                    'height': image_height,
                    'total_pixels': image_width * image_height
                },
                'color_analysis': self._serialize_analysis(color_analysis),
                'edge_analysis': self._serialize_analysis(edge_analysis),
                'texture_analysis': self._serialize_analysis(texture_analysis),
                'timestamp': time.time(),
                'version': '1.0.0'
            }

            # Store as parasite
            self._store_parasite(image, "ai-separation-analysis", analysis_data)

            Gimp.progress_update(1.0)

            # Show summary
            summary = self._create_summary_message(analysis_data)
            Gimp.message(summary)

            return procedure.new_return_values(
                Gimp.PDBStatusType.SUCCESS,
                GLib.Error()
            )

        except Exception as e:
            import traceback
            error_msg = f"Analysis failed:\n\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            Gimp.message(error_msg)
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(str(e))
            )

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

    def _serialize_analysis(self, analysis_result):
        """
        Convert analysis result to JSON-serializable dict

        Args:
            analysis_result: Analysis result object

        Returns:
            Dictionary with serialized data
        """
        if hasattr(analysis_result, '__dict__'):
            # Convert dataclass to dict
            result_dict = {}
            for key, value in analysis_result.__dict__.items():
                if isinstance(value, (int, float, str, bool, type(None))):
                    result_dict[key] = value
                elif isinstance(value, (list, tuple)):
                    result_dict[key] = list(value)
                elif isinstance(value, dict):
                    result_dict[key] = value
                elif hasattr(value, '__dict__'):
                    # Nested dataclass
                    result_dict[key] = self._serialize_analysis(value)
                else:
                    result_dict[key] = str(value)
            return result_dict
        else:
            return analysis_result

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

    def _create_summary_message(self, analysis_data):
        """
        Create user-friendly summary message

        Args:
            analysis_data: Analysis results dictionary

        Returns:
            Formatted summary string
        """
        color_analysis = analysis_data.get('color_analysis', {})
        edge_analysis = analysis_data.get('edge_analysis', {})
        texture_analysis = analysis_data.get('texture_analysis', {})

        summary = "Image Analysis Complete!\n\n"
        summary += "="*40 + "\n\n"

        # Color analysis
        summary += "COLOR ANALYSIS:\n"
        summary += f"  Unique colors: {color_analysis.get('unique_color_count', 'N/A')}\n"
        summary += f"  Color complexity: {color_analysis.get('color_complexity', 0):.2f}\n"

        gradient_info = color_analysis.get('gradient_analysis', {})
        summary += f"  Gradients present: {gradient_info.get('gradient_present', False)}\n"
        summary += "\n"

        # Edge analysis
        summary += "EDGE ANALYSIS:\n"
        summary += f"  Edge type: {edge_analysis.get('edge_type', 'unknown')}\n"
        summary += f"  Line work score: {edge_analysis.get('line_work_score', 0):.2f}\n"
        summary += "\n"

        # Texture analysis
        summary += "TEXTURE ANALYSIS:\n"
        summary += f"  Texture type: {texture_analysis.get('texture_type', 'unknown')}\n"

        halftone_info = texture_analysis.get('halftone_analysis', {})
        summary += f"  Halftone detected: {halftone_info.get('halftone_detected', False)}\n"
        summary += "\n"

        summary += "="*40 + "\n"
        summary += "Next: Run 'Color Match (Step 2)'"

        return summary


# GIMP plugin entry point
Gimp.main(AnalyzePlugin.__gtype__, sys.argv)
