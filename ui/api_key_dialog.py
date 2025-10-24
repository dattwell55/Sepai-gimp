#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api_key_dialog.py - Dialog for entering/managing Gemini API key

Provides a GTK dialog for users to enter and save their Gemini API key
without manually creating the config file.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import os


class ApiKeyDialog(Gtk.Dialog):
    """
    Dialog for entering and saving Gemini API key
    """

    def __init__(self, parent=None, current_key=None):
        """
        Initialize API key dialog

        Args:
            parent: Parent window (optional)
            current_key: Current API key if one exists (optional)
        """
        super().__init__(
            title="Gemini API Key Configuration",
            parent=parent,
            flags=0
        )

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(500, 250)
        self.current_key = current_key

        # Build UI
        self.init_ui()

    def init_ui(self):
        """Build the dialog UI"""
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)

        # Header
        header_label = Gtk.Label()
        header_label.set_markup(
            "<big><b>Gemini API Key Configuration</b></big>"
        )
        header_label.set_halign(Gtk.Align.START)
        box.pack_start(header_label, False, False, 0)

        # Info text
        info_label = Gtk.Label()
        info_label.set_markup(
            "The Gemini API key enables AI-powered features:\n"
            "• Intelligent method recommendations\n"
            "• Region-based analysis for Hybrid AI\n"
            "• Palette optimization\n\n"
            "<b>Get your free API key:</b> https://makersuite.google.com/app/apikey"
        )
        info_label.set_halign(Gtk.Align.START)
        info_label.set_line_wrap(True)
        box.pack_start(info_label, False, False, 5)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(separator, False, False, 5)

        # API Key entry
        key_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        key_label = Gtk.Label(label="API Key:")
        key_label.set_width_chars(10)
        key_box.pack_start(key_label, False, False, 0)

        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("Enter your Gemini API key here...")
        self.key_entry.set_visibility(False)  # Hide key like password
        self.key_entry.set_invisible_char('•')

        if self.current_key:
            self.key_entry.set_text(self.current_key)

        key_box.pack_start(self.key_entry, True, True, 0)

        # Toggle visibility button
        self.show_button = Gtk.ToggleButton(label="Show")
        self.show_button.connect("toggled", self.on_show_toggled)
        key_box.pack_start(self.show_button, False, False, 0)

        box.pack_start(key_box, False, False, 0)

        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_halign(Gtk.Align.START)
        box.pack_start(self.status_label, False, False, 5)

        if self.current_key:
            self.status_label.set_markup(
                '<span foreground="green">✓ API key currently configured</span>'
            )
        else:
            self.status_label.set_markup(
                '<span foreground="orange">⚠ No API key configured (plugins will use fallback mode)</span>'
            )

        # Info about fallback
        fallback_label = Gtk.Label()
        fallback_label.set_markup(
            '<small><i>Note: All features work without an API key using rule-based fallbacks.</i></small>'
        )
        fallback_label.set_halign(Gtk.Align.START)
        fallback_label.set_line_wrap(True)
        box.pack_start(fallback_label, False, False, 0)

        # Test button
        test_button = Gtk.Button(label="Test API Key")
        test_button.connect("clicked", self.on_test_clicked)
        box.pack_start(test_button, False, False, 5)

        self.show_all()

    def on_show_toggled(self, button):
        """Toggle API key visibility"""
        if button.get_active():
            self.key_entry.set_visibility(True)
            button.set_label("Hide")
        else:
            self.key_entry.set_visibility(False)
            button.set_label("Show")

    def on_test_clicked(self, button):
        """Test the API key"""
        api_key = self.key_entry.get_text().strip()

        if not api_key:
            self.status_label.set_markup(
                '<span foreground="red">✗ Please enter an API key</span>'
            )
            return

        # Try to test the key
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            # Try a simple test
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content("Say 'test successful' if you can read this.")

            if response:
                self.status_label.set_markup(
                    '<span foreground="green">✓ API key is valid and working!</span>'
                )
            else:
                self.status_label.set_markup(
                    '<span foreground="orange">⚠ API key accepted but no response</span>'
                )

        except ImportError:
            self.status_label.set_markup(
                '<span foreground="orange">⚠ Cannot test: google-generativeai not installed</span>'
            )
        except Exception as e:
            self.status_label.set_markup(
                f'<span foreground="red">✗ API key test failed: {str(e)[:50]}...</span>'
            )

    def get_api_key(self):
        """
        Get the entered API key

        Returns:
            API key string or None if empty
        """
        key = self.key_entry.get_text().strip()
        return key if key else None

    @staticmethod
    def get_config_path():
        """
        Get the path to the API key config file

        Returns:
            Path to gemini_api.key file
        """
        config_dir = os.path.join(
            GLib.get_user_config_dir(),
            'GIMP', '3.0', 'ai-separation'
        )

        # Create directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)

        return os.path.join(config_dir, 'gemini_api.key')

    @staticmethod
    def save_api_key(api_key):
        """
        Save API key to config file

        Args:
            api_key: API key to save

        Returns:
            True if successful, False otherwise
        """
        try:
            config_path = ApiKeyDialog.get_config_path()

            with open(config_path, 'w') as f:
                f.write(api_key)

            print(f"API key saved to: {config_path}")
            return True

        except Exception as e:
            print(f"Error saving API key: {e}")
            return False

    @staticmethod
    def load_api_key():
        """
        Load API key from config file

        Returns:
            API key string or None if not found
        """
        try:
            config_path = ApiKeyDialog.get_config_path()

            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return f.read().strip()

        except Exception as e:
            print(f"Error loading API key: {e}")

        return None


def show_api_key_dialog(parent=None):
    """
    Show API key dialog and save the result

    Args:
        parent: Parent window (optional)

    Returns:
        Tuple of (api_key, saved) where saved is True if key was saved
    """
    current_key = ApiKeyDialog.load_api_key()

    dialog = ApiKeyDialog(parent, current_key)
    response = dialog.run()

    api_key = None
    saved = False

    if response == Gtk.ResponseType.OK:
        api_key = dialog.get_api_key()

        if api_key:
            saved = ApiKeyDialog.save_api_key(api_key)

            if saved:
                message = Gtk.MessageDialog(
                    parent=parent,
                    flags=0,
                    type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="API Key Saved!"
                )
                message.format_secondary_text(
                    f"Your Gemini API key has been saved.\n\n"
                    f"Location: {ApiKeyDialog.get_config_path()}\n\n"
                    f"AI features are now enabled!"
                )
                message.run()
                message.destroy()
        else:
            # User clicked OK with empty key - remove existing key
            config_path = ApiKeyDialog.get_config_path()
            if os.path.exists(config_path):
                os.remove(config_path)
                saved = True

    dialog.destroy()

    return api_key, saved


# Test function
if __name__ == "__main__":
    # Test the dialog
    api_key, saved = show_api_key_dialog()

    if saved:
        print(f"API key saved successfully")
    else:
        print(f"API key not saved")
