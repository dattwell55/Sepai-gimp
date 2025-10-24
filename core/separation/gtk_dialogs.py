"""
gtk_dialogs.py - GTK UI for Separation method selection
Phase 3: User Interface
"""

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False
    print("Warning: GTK 3.0 not available. UI dialogs will not work.")
    # Create dummy Gtk class for testing
    class Gtk:
        class Dialog:
            pass
        class ResponseType:
            OK = 1
            CANCEL = 0

from .separation_data import SeparationMethod


class SeparationDialog(Gtk.Dialog if GTK_AVAILABLE else object):
    """Main separation method selection dialog"""

    def __init__(self, recommendations, palette):
        """
        Initialize separation dialog

        Args:
            recommendations: Dict with 'recommended', 'alternatives', 'all_methods'
            palette: List of color dictionaries
        """
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK 3.0 is required for dialogs")

        super().__init__(
            title="AI Color Separation - Method Selection",
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )

        self.recommendations = recommendations
        self.palette = palette
        self.selected_method = recommendations['recommended'].method if recommendations['recommended'] else None

        self.set_default_size(800, 600)
        self.set_border_width(10)

        self.init_ui()

    def init_ui(self):
        """Build the UI"""
        box = self.get_content_area()
        box.set_spacing(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Header
        header = Gtk.Label()
        header.set_markup("<b><big>Choose Separation Method</big></b>")
        header.set_halign(Gtk.Align.START)
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

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(6)
        vbox.set_margin_bottom(6)

        rec = self.recommendations['recommended']

        if not rec:
            label = Gtk.Label(label="No recommendations available")
            vbox.pack_start(label, False, False, 0)
            frame.add(vbox)
            return frame

        # Method name and confidence
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        method_label = Gtk.Label()
        method_label.set_markup(f"<b>{rec.method_name}</b>")
        method_label.set_halign(Gtk.Align.START)
        hbox.pack_start(method_label, True, True, 0)

        confidence_label = Gtk.Label()
        confidence_label.set_markup(f"<i>Confidence: {int(rec.confidence * 100)}%</i>")
        hbox.pack_start(confidence_label, False, False, 0)

        vbox.pack_start(hbox, False, False, 0)

        # Reasoning
        reasoning_label = Gtk.Label(label=rec.reasoning)
        reasoning_label.set_line_wrap(True)
        reasoning_label.set_halign(Gtk.Align.START)
        reasoning_label.set_max_width_chars(80)
        vbox.pack_start(reasoning_label, False, False, 0)

        # Expected results
        results_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)

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
        scrolled.set_min_content_height(300)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
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
            details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            details_box.set_margin_start(32)

            # Score bar
            score_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            score_label = Gtk.Label(label=f"Score: {int(method.score)}/100")
            score_hbox.pack_start(score_label, False, False, 0)

            score_bar = Gtk.ProgressBar()
            score_bar.set_fraction(method.score / 100)
            score_bar.set_show_text(False)
            score_bar.set_hexpand(True)
            score_hbox.pack_start(score_bar, True, True, 0)

            details_box.pack_start(score_hbox, False, False, 0)

            # Best for
            best_for_label = Gtk.Label()
            best_for_label.set_markup(f"<i>{method.best_for}</i>")
            best_for_label.set_line_wrap(True)
            best_for_label.set_halign(Gtk.Align.START)
            best_for_label.set_max_width_chars(80)
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

        self.params_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.params_vbox.set_margin_start(12)
        self.params_vbox.set_margin_end(12)
        self.params_vbox.set_margin_top(6)
        self.params_vbox.set_margin_bottom(6)

        # Initial parameters for recommended method
        if self.recommendations['recommended']:
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
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.pack_start(Gtk.Label(label="Color Tolerance:"), False, False, 0)

            self.tolerance_adj = Gtk.Adjustment(value=10, lower=1, upper=30, step_increment=1)
            tolerance_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.tolerance_adj)
            tolerance_scale.set_hexpand(True)
            tolerance_scale.set_digits(0)
            tolerance_scale.set_value_pos(Gtk.PositionType.RIGHT)
            hbox.pack_start(tolerance_scale, True, True, 0)

            self.params_vbox.pack_start(hbox, False, False, 0)

        elif method.method == SeparationMethod.SIMULATED_PROCESS:
            # Halftone method
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.pack_start(Gtk.Label(label="Halftone Method:"), False, False, 0)

            self.halftone_combo = Gtk.ComboBoxText()
            self.halftone_combo.append_text("Stochastic")
            self.halftone_combo.append_text("Error Diffusion")
            self.halftone_combo.set_active(0)
            hbox.pack_start(self.halftone_combo, True, True, 0)

            self.params_vbox.pack_start(hbox, False, False, 0)

        elif method.method == SeparationMethod.INDEX_COLOR:
            # Dither method
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.pack_start(Gtk.Label(label="Dither Method:"), False, False, 0)

            self.dither_combo = Gtk.ComboBoxText()
            self.dither_combo.append_text("Floyd-Steinberg")
            self.dither_combo.append_text("None")
            self.dither_combo.set_active(0)
            hbox.pack_start(self.dither_combo, True, True, 0)

            self.params_vbox.pack_start(hbox, False, False, 0)

        elif method.method in [SeparationMethod.CMYK, SeparationMethod.RGB]:
            # No parameters
            label = Gtk.Label(label="No adjustable parameters for this method")
            label.set_halign(Gtk.Align.START)
            self.params_vbox.pack_start(label, False, False, 0)

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
            if hasattr(self, 'tolerance_adj'):
                params['color_tolerance'] = self.tolerance_adj.get_value()
        elif self.selected_method == SeparationMethod.SIMULATED_PROCESS:
            if hasattr(self, 'halftone_combo'):
                params['halftone_method'] = self.halftone_combo.get_active_text().lower().replace(' ', '_')
        elif self.selected_method == SeparationMethod.INDEX_COLOR:
            if hasattr(self, 'dither_combo'):
                text = self.dither_combo.get_active_text()
                params['dither_method'] = text.lower().replace('-', '_').replace(' ', '_')

        return params

    def _create_info_label(self, title, value):
        """Create info label pair"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        title_label = Gtk.Label()
        title_label.set_markup(f"<small><b>{title}</b></small>")
        vbox.pack_start(title_label, False, False, 0)

        value_label = Gtk.Label(label=value)
        vbox.pack_start(value_label, False, False, 0)

        return vbox


def create_test_dialog():
    """Create a test dialog for development/testing"""
    from .separation_data import MethodRecommendation

    # Mock recommendations
    recommendations = {
        'recommended': MethodRecommendation(
            method=SeparationMethod.SPOT_COLOR,
            method_name='Spot Color',
            score=90.0,
            confidence=0.9,
            reasoning='Sharp edges and flat colors are ideal for spot color separation',
            strengths=['Crisp edges', 'Accurate colors', 'Cost-effective'],
            limitations=['Cannot handle gradients'],
            best_for='Logos, graphics, text with solid colors',
            expected_results={
                'channel_count': 4,
                'quality': 'excellent',
                'complexity': 'low',
                'cost': 'low'
            },
            palette_utilization={
                'colors_used': 4,
                'colors_total': 4,
                'percentage': 100.0
            }
        ),
        'alternatives': [
            MethodRecommendation(
                method=SeparationMethod.INDEX_COLOR,
                method_name='Index Color',
                score=75.0,
                confidence=0.75,
                reasoning='Alternative with moderate complexity',
                strengths=['Balanced quality/cost'],
                limitations=['Some banding'],
                best_for='Illustrations with moderate gradients',
                expected_results={
                    'channel_count': 4,
                    'quality': 'good',
                    'complexity': 'moderate',
                    'cost': 'medium'
                },
                palette_utilization={
                    'colors_used': 4,
                    'colors_total': 4,
                    'percentage': 100.0
                }
            )
        ],
        'all_methods': []
    }

    # Add all to all_methods
    recommendations['all_methods'] = [
        recommendations['recommended'],
        recommendations['alternatives'][0],
    ]

    # Mock palette
    palette = [
        {'name': 'Red', 'rgb': (255, 0, 0)},
        {'name': 'Blue', 'rgb': (0, 0, 255)},
        {'name': 'Green', 'rgb': (0, 255, 0)},
        {'name': 'Yellow', 'rgb': (255, 255, 0)},
    ]

    return SeparationDialog(recommendations, palette)
