#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
separation_plugin.py - GIMP AI Color Separation Plugin (Step 3: Separate Colors)

This is the GIMP 3.0 plugin wrapper for the Separation module.
It integrates with GIMP to provide AI-powered color separation for screen printing.

Usage:
1. Run "Analyze Image (Step 1)" first
2. Run "Color Match (Step 2)" second
3. Run this plugin: Filters > AI Separation > Separate Colors (Step 3)

Requirements:
- GIMP 3.0+
- Python 3.7+
- numpy
- scipy
- gi (PyGObject)
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
import time

# Add plugin directory to path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(plugin_dir, 'core'))

# Import separation modules
try:
    from separation import (
        AIMethodAnalyzer,
        SeparationCoordinator,
        SeparationMethod
    )
    SEPARATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Separation modules not available: {e}")
    SEPARATION_AVAILABLE = False

# Try to import GTK dialogs (Phase 3)
try:
    from separation.gtk_dialogs import SeparationDialog, GTK_AVAILABLE
    DIALOGS_AVAILABLE = GTK_AVAILABLE
except ImportError:
    print("Warning: GTK dialogs not available")
    DIALOGS_AVAILABLE = False


class SeparationPlugin(Gimp.PlugIn):
    """
    GIMP plugin wrapper for AI Color Separation - Step 3: Separate Colors
    """

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

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_menu_label("Separate Colors (Step 3)")
        procedure.add_menu_path('<Image>/Filters/AI Separation')

        procedure.set_documentation(
            "AI-powered color separation for screen printing",
            "Separate image into screen-printable layers using AI-recommended methods. "
            "This is Step 3 of the AI Color Separation workflow. "
            "Run 'Analyze Image' and 'Color Match' first.",
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
        Execute AI-powered color separation

        Workflow:
        1. Check for required data from Steps 1 & 2
        2. Get AI method recommendations
        3. Show dialog for user to select method
        4. Execute separation
        5. Create GIMP layers for each channel
        """
        try:
            # Check if separation modules available
            if not SEPARATION_AVAILABLE:
                Gimp.message("Separation modules not found. Please check installation.")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.EXECUTION_ERROR,
                    GLib.Error("Separation modules not available")
                )

            # Check for required data from previous steps
            Gimp.progress_init("Checking prerequisites...")

            analysis_data = self.get_parasite_data(image, "ai-separation-analysis")
            palette_data = self.get_parasite_data(image, "ai-separation-palette")

            if not analysis_data:
                Gimp.message("Analysis data not found.\n\nPlease run 'Analyze Image (Step 1)' first.")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error("Analysis data not found - run Step 1 first")
                )

            if not palette_data:
                Gimp.message("Palette data not found.\n\nPlease run 'Color Match (Step 2)' first.")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error("Palette data not found - run Step 2 first")
                )

            # Get Gemini API key (optional)
            api_key = self.get_api_key()

            # Convert drawable to numpy array
            Gimp.progress_init("Loading image...")
            drawable = drawables[0]
            rgb_array = self._drawable_to_numpy(drawable)

            # Get AI method recommendations
            Gimp.progress_init("Analyzing separation methods...")
            Gimp.progress_update(0.3)

            method_analyzer = AIMethodAnalyzer(api_key)
            recommendations = method_analyzer.analyze_and_recommend(
                analysis_data=analysis_data,
                palette_data=palette_data
            )

            Gimp.progress_update(0.6)

            # Show dialog for method selection
            if DIALOGS_AVAILABLE and run_mode == Gimp.RunMode.INTERACTIVE:
                # Use GTK dialog
                dialog = SeparationDialog(
                    recommendations=recommendations,
                    palette=palette_data['colors']
                )

                response = dialog.run()

                if response == Gtk.ResponseType.OK:
                    selected_method = dialog.get_selected_method()
                    parameters = dialog.get_parameters()
                    dialog.destroy()
                else:
                    dialog.destroy()
                    return procedure.new_return_values(
                        Gimp.PDBStatusType.CANCEL,
                        GLib.Error("User cancelled")
                    )
            else:
                # Non-interactive or no GTK - use recommended method
                selected_method = recommendations['recommended'].method
                parameters = {}
                Gimp.message(f"Using recommended method: {selected_method.value}")

            # Execute separation
            Gimp.progress_init(f"Separating with {selected_method.value}...")
            Gimp.progress_update(0.7)

            coordinator = SeparationCoordinator(api_key)
            result = coordinator.execute_separation(
                rgb_array=rgb_array,
                method=selected_method,
                palette=palette_data['colors'],
                analysis_data=analysis_data,
                parameters=parameters
            )

            Gimp.progress_update(0.9)

            if result.success:
                # Create GIMP layers from channels
                Gimp.progress_init("Creating layers...")
                self._create_layers_from_channels(
                    image,
                    result.channels,
                    palette_data['colors']
                )

                # Update display
                Gimp.displays_flush()

                Gimp.progress_update(1.0)
                Gimp.message(f"Separation complete!\n\n"
                            f"Created {len(result.channels)} color separation layers.\n"
                            f"Processing time: {result.processing_time:.2f}s\n"
                            f"Check the Layers panel.")

                return procedure.new_return_values(
                    Gimp.PDBStatusType.SUCCESS,
                    GLib.Error()
                )
            else:
                Gimp.message(f"Separation failed.\n\n{result.error_message}")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.EXECUTION_ERROR,
                    GLib.Error("Separation execution failed")
                )

        except Exception as e:
            import traceback
            error_msg = f"Separation plugin error:\n\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            Gimp.message(error_msg)
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(str(e))
            )

    def get_parasite_data(self, image, parasite_name):
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

    def get_api_key(self):
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

    def _create_layers_from_channels(self, image, channels, palette):
        """
        Create GIMP layers from separation channels

        Args:
            image: GIMP image
            channels: List of SeparationChannel objects
            palette: Color palette list
        """
        # Create layer group for separations
        layer_group = Gimp.LayerGroup.new(image)
        layer_group.set_name("Color Separations")
        image.insert_layer(layer_group, None, 0)

        # Create layer for each channel
        for idx, channel in enumerate(channels):
            # Find matching color info from palette
            color_info = None
            for color in palette:
                if color.get('name') == channel.name:
                    color_info = color
                    break

            # Create layer
            layer = self._create_layer_from_channel(
                image,
                channel,
                color_info
            )

            # Add to group
            image.insert_layer(layer, layer_group, idx)

            # Update progress
            Gimp.progress_update(0.9 + (0.1 * (idx + 1) / len(channels)))

        # Collapse group by default
        layer_group.set_expanded(False)

        print(f"Created {len(channels)} separation layers")

    def _create_layer_from_channel(self, image, channel, color_info=None):
        """
        Create a single GIMP layer from separation channel

        Args:
            image: GIMP image
            channel: SeparationChannel object
            color_info: Optional color information dict

        Returns:
            GIMP layer
        """
        channel_data = channel.data
        height, width = channel_data.shape

        # Create new grayscale layer
        layer = Gimp.Layer.new(
            image,
            channel.name,
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

        # Store metadata as parasites
        if color_info:
            # Store color info
            color_parasite = Gimp.Parasite.new(
                "separation-color",
                Gimp.ParasiteFlags.PERSISTENT,
                json.dumps(color_info).encode('utf-8')
            )
            layer.attach_parasite(color_parasite)

        # Store separation metadata
        metadata = {
            'order': channel.order,
            'halftone_angle': channel.halftone_angle,
            'halftone_frequency': channel.halftone_frequency,
            'pixel_count': channel.pixel_count,
            'coverage_percentage': channel.coverage_percentage
        }
        metadata_parasite = Gimp.Parasite.new(
            "separation-metadata",
            Gimp.ParasiteFlags.PERSISTENT,
            json.dumps(metadata).encode('utf-8')
        )
        layer.attach_parasite(metadata_parasite)

        return layer


# GIMP plugin entry point
Gimp.main(SeparationPlugin.__gtype__, sys.argv)
