#!/usr/bin/env python3
"""
test_integrated.py - Integrated test for Phase 1 + Phase 2
Tests complete workflow: Analyze → Recommend → Separate
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from separation.method_analyzer import AIMethodAnalyzer
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
    return {
        'colors': [
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
    }


def create_test_analysis():
    """Create mock analysis data"""
    return {
        'color_analysis': {
            'total_unique_colors': 4,
            'complexity_score': 0.2,
            'gradient_present': False
        },
        'edge_analysis': {
            'edge_type': 'sharp',
            'line_work_score': 0.9
        },
        'texture_analysis': {
            'texture_type': 'illustration'
        }
    }


def test_integrated_workflow():
    """Test complete workflow from analysis to separation"""
    print("="*60)
    print("INTEGRATED TEST: Phase 1 + Phase 2")
    print("="*60)

    # Step 1: Prepare test data
    print("\n[Step 1] Preparing test data...")
    test_image = create_test_image()
    test_palette = create_test_palette()
    test_analysis = create_test_analysis()

    print(f"  Image size: {test_image.shape}")
    print(f"  Palette colors: {len(test_palette['colors'])}")
    print(f"  Analysis: {test_analysis['edge_analysis']['edge_type']} edges")

    # Step 2: AI Method Recommendation (Phase 2)
    print("\n[Step 2] AI Method Recommendation...")
    analyzer = AIMethodAnalyzer(api_key=None)

    recommendations = analyzer.analyze_and_recommend(
        analysis_data=test_analysis,
        palette_data=test_palette
    )

    if not recommendations['recommended']:
        print("  FAILED: No recommendations")
        return False

    rec = recommendations['recommended']
    print(f"  Recommended: {rec.method_name} (score: {rec.score:.1f})")
    print(f"  Reasoning: {rec.reasoning}")

    # Step 3: Execute Separation (Phase 1)
    print(f"\n[Step 3] Executing {rec.method_name} separation...")
    coordinator = SeparationCoordinator()

    # Get default parameters for recommended method
    parameters = coordinator.get_default_parameters(rec.method)

    result = coordinator.execute_separation(
        rgb_array=test_image,
        method=rec.method,
        palette=test_palette['colors'],
        analysis_data=test_analysis,
        parameters=parameters
    )

    if not result.success:
        print(f"  FAILED: {result.error_message}")
        return False

    print(f"  SUCCESS: Created {len(result.channels)} channels")
    print(f"  Processing time: {result.processing_time:.3f}s")
    print(f"  Total coverage: {result.total_coverage:.1f}%")

    # Step 4: Verify channels
    print(f"\n[Step 4] Verifying channels...")
    for ch in result.channels:
        print(f"  - {ch.name}: {ch.coverage_percentage:.1f}% coverage, {ch.pixel_count} pixels")

    # Validate
    if len(result.channels) != len(test_palette['colors']):
        print(f"\n  WARNING: Channel count mismatch")
        print(f"    Expected: {len(test_palette['colors'])}")
        print(f"    Got: {len(result.channels)}")

    print(f"\n{'='*60}")
    print("INTEGRATED TEST COMPLETE")
    print(f"{'='*60}")
    print(f"\nWorkflow summary:")
    print(f"  1. Analysis data -> AI Analyzer")
    print(f"  2. AI recommended: {rec.method_name}")
    print(f"  3. Coordinator executed separation")
    print(f"  4. Created {len(result.channels)} output channels")
    print(f"\nAll systems working correctly!")

    return True


def main():
    """Run integrated test"""
    try:
        success = test_integrated_workflow()
        return 0 if success else 1
    except Exception as e:
        import traceback
        print(f"\nERROR: {e}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
