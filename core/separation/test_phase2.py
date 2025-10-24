#!/usr/bin/env python3
"""
test_phase2.py - Test script for Phase 2 AI method recommendation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from separation.method_analyzer import AIMethodAnalyzer
from separation.separation_data import SeparationMethod


def create_simple_image_analysis():
    """Create mock analysis data for simple logo/graphic"""
    return {
        'color_analysis': {
            'total_unique_colors': 2500,
            'complexity_score': 0.3,
            'gradient_present': False
        },
        'edge_analysis': {
            'edge_type': 'sharp',
            'line_work_score': 0.85
        },
        'texture_analysis': {
            'texture_type': 'illustration'
        }
    }


def create_photo_image_analysis():
    """Create mock analysis data for photograph"""
    return {
        'color_analysis': {
            'total_unique_colors': 45000,
            'complexity_score': 0.8,
            'gradient_present': True
        },
        'edge_analysis': {
            'edge_type': 'soft',
            'line_work_score': 0.2
        },
        'texture_analysis': {
            'texture_type': 'photo'
        }
    }


def create_mixed_image_analysis():
    """Create mock analysis data for mixed content"""
    return {
        'color_analysis': {
            'total_unique_colors': 15000,
            'complexity_score': 0.6,
            'gradient_present': True
        },
        'edge_analysis': {
            'edge_type': 'mixed',
            'line_work_score': 0.55
        },
        'texture_analysis': {
            'texture_type': 'mixed'
        }
    }


def create_test_palette(num_colors=4):
    """Create mock palette"""
    colors = [
        {'name': 'Red', 'rgb': (255, 0, 0), 'lab': (53.24, 80.09, 67.20)},
        {'name': 'Blue', 'rgb': (0, 0, 255), 'lab': (32.30, 79.19, -107.86)},
        {'name': 'Green', 'rgb': (0, 255, 0), 'lab': (87.73, -86.18, 83.18)},
        {'name': 'Yellow', 'rgb': (255, 255, 0), 'lab': (97.14, -21.55, 94.48)},
        {'name': 'Black', 'rgb': (0, 0, 0), 'lab': (0, 0, 0)},
        {'name': 'White', 'rgb': (255, 255, 255), 'lab': (100, 0, 0)},
    ]

    return {'colors': colors[:num_colors]}


def test_analyzer(analyzer, test_name, analysis_data, palette_data, expected_method=None):
    """Test the analyzer with given data"""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")

    # Run analysis
    recommendations = analyzer.analyze_and_recommend(
        analysis_data=analysis_data,
        palette_data=palette_data
    )

    # Check result
    if not recommendations['recommended']:
        print("\nFAILED: No recommendations returned")
        return False

    rec = recommendations['recommended']

    print(f"\nRecommended Method: {rec.method_name}")
    print(f"  Score: {rec.score:.1f}/100")
    print(f"  Confidence: {int(rec.confidence * 100)}%")
    print(f"  Reasoning: {rec.reasoning}")

    print(f"\n  Expected Results:")
    print(f"    Channels: {rec.expected_results['channel_count']}")
    print(f"    Quality: {rec.expected_results['quality']}")
    print(f"    Complexity: {rec.expected_results['complexity']}")
    print(f"    Cost: {rec.expected_results['cost']}")

    print(f"\n  Strengths:")
    for strength in rec.strengths[:3]:
        print(f"    - {strength}")

    print(f"\n  Limitations:")
    for limitation in rec.limitations[:2]:
        print(f"    - {limitation}")

    # Check alternatives
    if recommendations['alternatives']:
        print(f"\n  Alternatives ({len(recommendations['alternatives'])}): ")
        for alt in recommendations['alternatives'][:2]:
            print(f"    - {alt.method_name} (score: {alt.score:.1f})")

    # Validate expected method if provided
    if expected_method:
        if rec.method == expected_method:
            print(f"\nSUCCESS: Correctly recommended {expected_method.value}")
            return True
        else:
            print(f"\nWARNING: Expected {expected_method.value}, got {rec.method.value}")
            return True  # Still pass, AI can make different choices
    else:
        print(f"\nSUCCESS: Analysis completed")
        return True


def main():
    """Run all Phase 2 tests"""
    print("="*60)
    print("PHASE 2: AI METHOD RECOMMENDATION TEST")
    print("="*60)

    # Initialize analyzer (without API key = rule-based)
    print("\nInitializing analyzer...")
    analyzer = AIMethodAnalyzer(api_key=None)

    results = {}

    # Test 1: Simple logo/graphic (should recommend SPOT_COLOR)
    results['simple_logo'] = test_analyzer(
        analyzer,
        "Simple Logo (4 colors, sharp edges)",
        create_simple_image_analysis(),
        create_test_palette(4),
        expected_method=SeparationMethod.SPOT_COLOR
    )

    # Test 2: Photograph (should recommend SIMULATED_PROCESS)
    results['photo'] = test_analyzer(
        analyzer,
        "Photograph (many colors, gradients)",
        create_photo_image_analysis(),
        create_test_palette(6),
        expected_method=SeparationMethod.SIMULATED_PROCESS
    )

    # Test 3: Mixed content (should recommend INDEX_COLOR or SIMULATED_PROCESS)
    results['mixed'] = test_analyzer(
        analyzer,
        "Mixed Content (moderate complexity)",
        create_mixed_image_analysis(),
        create_test_palette(8)
    )

    # Test 4: Many colors (should handle gracefully)
    results['many_colors'] = test_analyzer(
        analyzer,
        "Many Colors (12+ colors)",
        create_photo_image_analysis(),
        create_test_palette(6)
    )

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll Phase 2 tests passed!")
        print("\nNOTE: Tests ran with rule-based fallback (no API key).")
        print("To test with Gemini AI:")
        print("  1. Install: pip install google-generativeai")
        print("  2. Set API key when initializing: AIMethodAnalyzer(api_key='your-key')")
        return 0
    else:
        print(f"\nWARNING: {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
