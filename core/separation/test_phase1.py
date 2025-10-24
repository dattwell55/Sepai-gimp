#!/usr/bin/env python3
"""
test_phase1.py - Test script for Phase 1 separation engines
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from separation.separation_coordinator import SeparationCoordinator
from separation.separation_data import SeparationMethod


def create_test_image(width=100, height=100):
    """Create a simple test image with known colors"""
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # Red quarter
    img[0:50, 0:50] = [255, 0, 0]

    # Blue quarter
    img[0:50, 50:100] = [0, 0, 255]

    # Green quarter
    img[50:100, 0:50] = [0, 255, 0]

    # Yellow quarter
    img[50:100, 50:100] = [255, 255, 0]

    return img


def create_test_palette():
    """Create test palette matching the image colors"""
    return [
        {
            'name': 'Red',
            'rgb': (255, 0, 0),
            'lab': (53.24, 80.09, 67.20),
            'pantone_code': 'Red 032 C'
        },
        {
            'name': 'Blue',
            'rgb': (0, 0, 255),
            'lab': (32.30, 79.19, -107.86),
            'pantone_code': 'Blue 072 C'
        },
        {
            'name': 'Green',
            'rgb': (0, 255, 0),
            'lab': (87.73, -86.18, 83.18),
            'pantone_code': 'Green C'
        },
        {
            'name': 'Yellow',
            'rgb': (255, 255, 0),
            'lab': (97.14, -21.55, 94.48),
            'pantone_code': 'Yellow C'
        }
    ]


def test_engine(coordinator, method, test_image, test_palette, test_analysis):
    """Test a single separation engine"""
    print(f"\n{'='*60}")
    print(f"Testing: {method.value.upper()}")
    print(f"{'='*60}")

    # Get default parameters
    parameters = coordinator.get_default_parameters(method)
    print(f"Parameters: {parameters}")

    # Execute separation
    result = coordinator.execute_separation(
        rgb_array=test_image,
        method=method,
        palette=test_palette,
        analysis_data=test_analysis,
        parameters=parameters
    )

    # Check result
    if result.success:
        print(f"\nSUCCESS")
        print(f"  Channels created: {len(result.channels)}")
        print(f"  Processing time: {result.processing_time:.3f}s")
        print(f"  Total coverage: {result.total_coverage:.1f}%")

        print(f"\n  Channel Details:")
        for ch in result.channels:
            print(f"    - {ch.name}:")
            print(f"        Coverage: {ch.coverage_percentage:.1f}%")
            print(f"        Pixels: {ch.pixel_count}")
            print(f"        Color: {ch.color_info['hex']}")
            print(f"        Halftone: {ch.halftone_angle}° @ {ch.halftone_frequency} LPI")

        return True
    else:
        print(f"\nFAILED")
        print(f"  Error: {result.error_message}")
        return False


def main():
    """Run all Phase 1 tests"""
    print("="*60)
    print("PHASE 1: SEPARATION ENGINES TEST")
    print("="*60)

    # Create test data
    print("\nPreparing test data...")
    test_image = create_test_image()
    test_palette = create_test_palette()
    test_analysis = {
        'color_analysis': {},
        'edge_analysis': {},
        'texture_analysis': {}
    }

    print(f"  Image size: {test_image.shape}")
    print(f"  Palette colors: {len(test_palette)}")

    # Initialize coordinator
    coordinator = SeparationCoordinator()

    # Test each engine
    results = {}

    # Test 1: Spot Color
    results['spot_color'] = test_engine(
        coordinator,
        SeparationMethod.SPOT_COLOR,
        test_image,
        test_palette,
        test_analysis
    )

    # Test 2: Simulated Process
    results['simulated_process'] = test_engine(
        coordinator,
        SeparationMethod.SIMULATED_PROCESS,
        test_image,
        test_palette,
        test_analysis
    )

    # Test 3: Index Color
    results['index_color'] = test_engine(
        coordinator,
        SeparationMethod.INDEX_COLOR,
        test_image,
        test_palette,
        test_analysis
    )

    # Test 4: CMYK
    results['cmyk'] = test_engine(
        coordinator,
        SeparationMethod.CMYK,
        test_image,
        test_palette,
        test_analysis
    )

    # Test 5: RGB
    results['rgb'] = test_engine(
        coordinator,
        SeparationMethod.RGB,
        test_image,
        test_palette,
        test_analysis
    )

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for method_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {status}: {method_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll Phase 1 engines working correctly!")
        return 0
    else:
        print(f"\nWARNING: {total - passed} engine(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
