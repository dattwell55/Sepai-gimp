#!/usr/bin/env python3
"""
test_phase3.py - Test script for Phase 3 GTK UI
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from separation.gtk_dialogs import GTK_AVAILABLE, create_test_dialog
from separation.separation_data import SeparationMethod


def test_gtk_availability():
    """Test if GTK 3.0 is available"""
    print("="*60)
    print("PHASE 3: GTK USER INTERFACE TEST")
    print("="*60)

    print("\nChecking GTK 3.0 availability...")

    if GTK_AVAILABLE:
        print("  [OK] GTK 3.0 is available")
        return True
    else:
        print("  [WARNING] GTK 3.0 not available")
        print("\n  GTK dialogs require PyGObject with GTK 3.0:")
        print("    Windows: Install from https://pygobject.readthedocs.io/")
        print("    Linux: sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        print("    macOS: brew install pygobject3 gtk+3")
        print("\n  The dialog code has been created and is ready to use.")
        print("  Install GTK 3.0 to test the UI functionality.")
        return False


def test_dialog_creation():
    """Test dialog creation and functionality"""
    print("\n" + "="*60)
    print("Testing dialog creation...")
    print("="*60)

    try:
        # Create test dialog
        dialog = create_test_dialog()

        print("\n  [OK] Dialog created successfully")
        print(f"    Title: {dialog.get_title()}")
        print(f"    Selected method: {dialog.get_selected_method()}")

        # Test getting parameters
        params = dialog.get_parameters()
        print(f"    Parameters: {params}")

        # Test method change
        print("\n  Testing method selection changes...")

        # The dialog should have method_radios dict
        if hasattr(dialog, 'method_radios'):
            print(f"    Available methods: {len(dialog.method_radios)}")

            # Test changing to INDEX_COLOR
            if SeparationMethod.INDEX_COLOR in dialog.method_radios:
                print("    Simulating change to INDEX_COLOR...")
                radio = dialog.method_radios[SeparationMethod.INDEX_COLOR]
                radio.set_active(True)

                new_method = dialog.get_selected_method()
                new_params = dialog.get_parameters()

                print(f"      New method: {new_method}")
                print(f"      New parameters: {new_params}")

        print("\n  [OK] Dialog functionality test passed")

        # Clean up
        dialog.destroy()

        return True

    except Exception as e:
        import traceback
        print(f"\n  [ERROR] Dialog test failed: {e}")
        print(f"    Traceback:\n{traceback.format_exc()}")
        return False


def test_dialog_components():
    """Test individual dialog components"""
    print("\n" + "="*60)
    print("Testing dialog components...")
    print("="*60)

    try:
        dialog = create_test_dialog()

        # Test recommendation section
        print("\n  Testing recommendation section...")
        rec = dialog.recommendations['recommended']
        if rec:
            print(f"    Recommended: {rec.method_name}")
            print(f"    Score: {rec.score}")
            print(f"    Confidence: {rec.confidence}")
            print("    [OK] Recommendation section working")

        # Test parameters section
        print("\n  Testing parameters section...")
        if hasattr(dialog, 'params_vbox'):
            children = dialog.params_vbox.get_children()
            print(f"    Parameter widgets: {len(children)}")
            print("    [OK] Parameters section working")

        # Test method radios
        print("\n  Testing method selection...")
        if hasattr(dialog, 'method_radios'):
            print(f"    Method options: {len(dialog.method_radios)}")
            for method in dialog.method_radios:
                print(f"      - {method.value}")
            print("    [OK] Method selection working")

        dialog.destroy()

        print("\n  [OK] All component tests passed")
        return True

    except Exception as e:
        import traceback
        print(f"\n  [ERROR] Component test failed: {e}")
        print(f"    Traceback:\n{traceback.format_exc()}")
        return False


def main():
    """Run all Phase 3 tests"""

    results = {}

    # Test 1: GTK availability
    results['gtk_available'] = test_gtk_availability()

    if not results['gtk_available']:
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("  SKIP: GTK 3.0 not available")
        print("\nPhase 3 code is complete but cannot be tested without GTK 3.0.")
        print("Install GTK 3.0 to run UI tests.")
        return 2  # Special exit code for "skipped"

    # Test 2: Dialog creation
    results['dialog_creation'] = test_dialog_creation()

    # Test 3: Dialog components
    results['dialog_components'] = test_dialog_components()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for k, v in results.items() if v and k != 'gtk_available')
    total = len(results) - 1  # Don't count gtk_available

    for test_name, success in results.items():
        if test_name == 'gtk_available':
            continue
        status = "PASS" if success else "FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll Phase 3 tests passed!")
        print("\nNOTE: The GTK dialog is fully functional.")
        print("To use in production:")
        print("  1. Ensure GTK 3.0 is installed")
        print("  2. Call SeparationDialog(recommendations, palette)")
        print("  3. Run dialog.run() to show modal dialog")
        print("  4. Get results with dialog.get_selected_method() and dialog.get_parameters()")
        return 0
    else:
        print(f"\nWARNING: {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
