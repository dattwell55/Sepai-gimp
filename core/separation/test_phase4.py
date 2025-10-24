#!/usr/bin/env python3
"""
test_phase4.py - Test script for Phase 4 Hybrid AI Separation
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from separation import (
    SeparationMethod,
    SeparationCoordinator,
    HybridSeparationParameters,
    HybridAIEngine
)


def create_test_image_mixed_content():
    """Create test image with mixed content (vector + photo)"""
    img = np.zeros((400, 600, 3), dtype=np.uint8)

    # Region 1: Flat red rectangle (vector-like) - top half
    img[50:200, 100:300] = [255, 0, 0]

    # Region 2: Blue gradient (photo-like) - bottom half
    for i in range(250, 350):
        intensity = int(255 * (i - 250) / 100)
        img[i, 150:450] = [0, 0, intensity]

    # Region 3: Yellow text-like region (sharp edges)
    img[120:140, 350:500] = [255, 255, 0]

    return img


def create_test_image_logo_on_photo():
    """Create test image simulating logo on photograph"""
    img = np.zeros((500, 500, 3), dtype=np.uint8)

    # Background: Gradient (photo-like)
    for i in range(500):
        for j in range(500):
            img[i, j] = [
                int(100 + 100 * i / 500),
                int(80 + 80 * j / 500),
                int(120 + 80 * ((i + j) / 1000))
            ]

    # Overlay: Sharp logo (vector-like)
    img[150:250, 150:350] = [255, 0, 0]  # Red rectangle
    img[180:220, 200:300] = [255, 255, 255]  # White center

    return img


def rgb_to_lab(rgb_image):
    """Simple RGB to LAB conversion"""
    # Normalize RGB to 0-1
    rgb_norm = rgb_image.astype(np.float32) / 255.0

    # Simple approximation of LAB
    # L = luminance
    L = 0.299 * rgb_norm[:, :, 0] + 0.587 * rgb_norm[:, :, 1] + 0.114 * rgb_norm[:, :, 2]
    L = L * 100  # Scale to 0-100

    # A and B channels (simplified)
    A = (rgb_norm[:, :, 0] - rgb_norm[:, :, 1]) * 128
    B = (rgb_norm[:, :, 1] - rgb_norm[:, :, 2]) * 128

    return np.stack([L, A, B], axis=2)


def create_mock_palette():
    """Create mock color palette"""
    return [
        {'name': 'Red', 'rgb': (255, 0, 0), 'hex': '#ff0000', 'lab': (53, 80, 67)},
        {'name': 'Blue', 'rgb': (0, 0, 255), 'hex': '#0000ff', 'lab': (32, 79, -108)},
        {'name': 'Yellow', 'rgb': (255, 255, 0), 'hex': '#ffff00', 'lab': (97, -22, 94)},
        {'name': 'White', 'rgb': (255, 255, 255), 'hex': '#ffffff', 'lab': (100, 0, 0)},
    ]


def create_mock_analysis():
    """Create mock analysis data"""
    return {
        'color_analysis': {
            'total_unique_colors': 5000,
            'gradient_analysis': {
                'gradient_present': True,
                'gradient_smoothness': 0.7
            }
        },
        'edge_analysis': {
            'edge_type': 'mixed',
            'line_work_score': 0.6
        },
        'texture_analysis': {
            'texture_type': 'mixed',
            'halftone_analysis': {
                'halftone_detected': False
            }
        }
    }


def test_hybrid_parameters():
    """Test 1: Hybrid parameter creation"""
    print("\n" + "="*60)
    print("TEST 1: Hybrid Parameters")
    print("="*60)

    try:
        params = HybridSeparationParameters(
            min_region_size=1000,
            edge_sensitivity=0.5,
            blend_edges=True,
            blend_radius=15,
            prefer_spot_color=True,
            detail_level='high'
        )

        print(f"  Min region size: {params.min_region_size}")
        print(f"  Edge sensitivity: {params.edge_sensitivity}")
        print(f"  Blend edges: {params.blend_edges}")
        print(f"  Blend radius: {params.blend_radius}")
        print(f"  Detail level: {params.detail_level}")

        print("\n  [PASS] Hybrid parameters created successfully")
        return True

    except Exception as e:
        import traceback
        print(f"\n  [FAIL] Error: {e}")
        print(f"  {traceback.format_exc()}")
        return False


def test_hybrid_engine_init():
    """Test 2: Hybrid engine initialization"""
    print("\n" + "="*60)
    print("TEST 2: Hybrid Engine Initialization")
    print("="*60)

    try:
        # Without API key
        engine = HybridAIEngine(api_key=None)
        print("  [OK] Engine initialized without API key (rule-based mode)")

        # With fake API key
        engine_with_key = HybridAIEngine(api_key="test_key")
        print("  [OK] Engine initialized with API key")

        print("\n  [PASS] Hybrid engine initialization successful")
        return True

    except Exception as e:
        import traceback
        print(f"\n  [FAIL] Error: {e}")
        print(f"  {traceback.format_exc()}")
        return False


def test_hybrid_separation_mixed_content():
    """Test 3: Hybrid separation with mixed content"""
    print("\n" + "="*60)
    print("TEST 3: Hybrid Separation - Mixed Content")
    print("="*60)

    try:
        # Create test image
        print("  Creating test image (vector + photo)...")
        rgb_image = create_test_image_mixed_content()
        lab_image = rgb_to_lab(rgb_image)

        print(f"  Image shape: {rgb_image.shape}")

        # Create mock data
        palette = create_mock_palette()
        analysis = create_mock_analysis()

        # Create coordinator
        coordinator = SeparationCoordinator(api_key=None)  # No API key - use rule-based

        # Parameters
        parameters = {
            'min_region_size': 500,  # Smaller for test image
            'edge_sensitivity': 0.5,
            'blend_edges': True,
            'blend_radius': 10,
            'prefer_spot_color': True,
            'detail_level': 'medium'
        }

        print("\n  Executing hybrid separation...")

        # Execute
        result = coordinator.execute_separation(
            rgb_array=rgb_image,
            method=SeparationMethod.HYBRID_AI,
            palette=palette,
            analysis_data=analysis,
            parameters=parameters
        )

        print(f"\n  Success: {result.success}")
        print(f"  Channels created: {len(result.channels)}")

        if result.channels:
            for ch in result.channels:
                print(f"    - {ch.name}: {ch.coverage_percentage:.1f}% coverage")

        if result.success and len(result.channels) > 0:
            print("\n  [PASS] Hybrid separation completed successfully")
            return True
        else:
            print("\n  [FAIL] Hybrid separation did not produce channels")
            return False

    except Exception as e:
        import traceback
        print(f"\n  [FAIL] Error: {e}")
        print(f"  {traceback.format_exc()}")
        return False


def test_hybrid_separation_logo_on_photo():
    """Test 4: Hybrid separation with logo on photo"""
    print("\n" + "="*60)
    print("TEST 4: Hybrid Separation - Logo on Photo")
    print("="*60)

    try:
        # Create test image
        print("  Creating test image (logo on photo background)...")
        rgb_image = create_test_image_logo_on_photo()
        lab_image = rgb_to_lab(rgb_image)

        print(f"  Image shape: {rgb_image.shape}")

        # Create mock data
        palette = create_mock_palette()
        analysis = create_mock_analysis()

        # Create engine directly
        engine = HybridAIEngine(api_key=None)

        # Parameters
        parameters = {
            'min_region_size': 800,
            'edge_sensitivity': 0.6,
            'blend_edges': True,
            'blend_radius': 15,
            'prefer_spot_color': True,
            'detail_level': 'high'
        }

        print("\n  Executing hybrid separation...")

        # Execute
        channels = engine.separate(
            rgb_array=rgb_image,
            palette=palette,
            analysis_data=analysis,
            parameters=parameters
        )

        print(f"\n  Channels created: {len(channels)}")

        if channels:
            for ch in channels:
                print(f"    - {ch.name}: {ch.coverage_percentage:.1f}% coverage")

        if len(channels) > 0:
            print("\n  [PASS] Logo on photo separation successful")
            return True
        else:
            print("\n  [FAIL] No channels created")
            return False

    except Exception as e:
        import traceback
        print(f"\n  [FAIL] Error: {e}")
        print(f"  {traceback.format_exc()}")
        return False


def test_region_segmentation():
    """Test 5: Region segmentation only"""
    print("\n" + "="*60)
    print("TEST 5: Region Segmentation")
    print("="*60)

    try:
        from separation.region_segmenter import RegionSegmenter
        from separation.hybrid_data import HybridSeparationParameters

        # Create test image
        rgb_image = create_test_image_mixed_content()
        lab_image = rgb_to_lab(rgb_image)
        analysis = create_mock_analysis()

        # Create segmenter
        segmenter = RegionSegmenter()
        params = HybridSeparationParameters(min_region_size=500)

        print("  Running segmentation...")

        # Segment
        regions = segmenter.segment_image(
            rgb_image=rgb_image,
            lab_image=lab_image,
            analysis_data=analysis,
            parameters=params
        )

        print(f"\n  Regions found: {len(regions)}")

        for region in regions:
            print(f"    - {region['region_id']}: {region['type']}, "
                  f"{region['coverage']:.1f}% coverage, "
                  f"edge sharpness {region['edge_sharpness']:.2f}")

        if len(regions) > 0:
            print("\n  [PASS] Region segmentation successful")
            return True
        else:
            print("\n  [FAIL] No regions found")
            return False

    except Exception as e:
        import traceback
        print(f"\n  [FAIL] Error: {e}")
        print(f"  {traceback.format_exc()}")
        return False


def main():
    """Run all Phase 4 tests"""

    print("="*60)
    print("PHASE 4: HYBRID AI SEPARATION - TESTS")
    print("="*60)

    results = {}

    # Run all tests
    results['hybrid_parameters'] = test_hybrid_parameters()
    results['hybrid_engine_init'] = test_hybrid_engine_init()
    results['region_segmentation'] = test_region_segmentation()
    results['mixed_content'] = test_hybrid_separation_mixed_content()
    results['logo_on_photo'] = test_hybrid_separation_logo_on_photo()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*60)
        print("PHASE 4: HYBRID AI SEPARATION COMPLETE")
        print("="*60)
        print("\nAll Phase 4 tests passed!")
        print("\nKey features implemented:")
        print("  - Region segmentation (edge, color, texture)")
        print("  - AI region analysis (with rule-based fallback)")
        print("  - Per-region separation with appropriate methods")
        print("  - Channel blending and merging")
        print("  - Complete hybrid engine integration")
        print("\nStatus:")
        print("  - Phase 1: COMPLETE (5/5 engines)")
        print("  - Phase 2: COMPLETE (AI recommendation)")
        print("  - Phase 3: COMPLETE (GTK UI)")
        print("  - Phase 4: COMPLETE (Hybrid AI)")
        print("\nNext: Phase 5 (GIMP Plugin Wrapper)")
        return 0
    else:
        print(f"\nWARNING: {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
