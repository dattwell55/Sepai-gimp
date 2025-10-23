# GIMP AI Color Separation Plugin - Analyze Module Specification
# Version: 1.0-GIMP
# Date: January 2025
# Status: Draft for Review

## Overview

The Analyze module is the first component of the AI Color Separation GIMP plugin. It performs silent background analysis of image characteristics, extracting color, edge, and texture data needed for intelligent palette generation and separation.

## Architecture Changes from Standalone

### What Stays (95% of existing code)
- All analysis algorithms (color, edge, texture)
- Data structures (ProcessedImageData, AnalysisDataModel)
- Caching logic via GlobalState
- Multi-resolution strategy
- Re-analysis thresholds

### What Changes
- Image data acquisition: GIMP API instead of file loading
- No separate LOAD unit - GIMP handles file I/O
- Direct integration with GIMP's image/layer system
- Simplified ProcessedImageData creation

## Module Structure
```
gimp-ai-separation/
├── analyze/
│   ├── __init__.py
│   ├── analyze_plugin.py      # GIMP plugin wrapper (NEW)
│   ├── analyze_unit.py        # Core analysis (EXISTING v1.1)
│   ├── color_analysis.py      # Color module (EXISTING)
│   ├── edge_analysis.py       # Edge module (EXISTING)
│   ├── texture_analysis.py    # Texture module (EXISTING)
│   └── data_structures.py     # Data models (EXISTING)
```

## GIMP Plugin Integration

### Plugin Registration
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_plugin.py - GIMP interface for Analyze module
"""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp, GObject, GLib
import numpy as np
import sys
import os

# Add plugin directory to path for imports
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_dir)

from analyze.analyze_unit import AnalyzeUnitCoordinator
from analyze.data_structures import ProcessedImageData, ImageDimensions

class AnalyzePlugin(Gimp.PlugIn):
    """GIMP plugin wrapper for Analyze module"""
    
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
        
        procedure.set_menu_label("Analyze Image (Step 1)")
        procedure.add_menu_path('<Image>/Filters/AI Separation/')
        
        procedure.set_documentation(
            "Analyze image characteristics",
            "Performs color, edge, and texture analysis for AI separation",
            name
        )
        
        procedure.set_attribution(
            "Your Name",
            "Copyright 2025",
            "2025"
        )
        
        return procedure
    
    def run(self, procedure, run_mode, image, n_drawables, drawables, config, data):
        """Execute analysis"""
        try:
            # Extract image data from GIMP
            processed_data = self.extract_image_data(image, drawables[0])
            
            # Run analysis (silent, no UI)
            analyzer = AnalyzeUnitCoordinator()
            analysis_model = analyzer.process(processed_data)
            
            # Store results in GIMP parasite for next steps
            self.store_analysis_results(image, analysis_model)
            
            # Success message (minimal UI)
            Gimp.message("Analysis complete. Ready for Color Match.")
            
            return procedure.new_return_values(
                Gimp.PDBStatusType.SUCCESS, 
                GLib.Error()
            )
            
        except Exception as e:
            Gimp.message(f"Analysis failed: {str(e)}")
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(f"Analysis failed: {str(e)}")
            )
    
    def extract_image_data(self, image, drawable):
        """Convert GIMP image to ProcessedImageData"""
        
        # Get dimensions
        width = drawable.get_width()
        height = drawable.get_height()
        
        # Get pixel buffer
        buffer = drawable.get_buffer()
        
        # Extract as numpy array
        rgb_array = self.buffer_to_numpy(buffer, width, height)
        
        # Convert RGB to LAB
        lab_array = self.rgb_to_lab(rgb_array)
        
        # Create ProcessedImageData
        dimensions = ImageDimensions(
            original_width=width,
            original_height=height,
            original_dpi=image.get_resolution()[0],  # X resolution
            working_width=min(width, 800),
            working_height=min(height, 600)
        )
        
        processed_data = ProcessedImageData(
            rgb_image=rgb_array,
            lab_image=lab_array,
            dimensions=dimensions,
            source_filename=image.get_filename() or "untitled",
            source_filepath=image.get_filename() or ""
        )
        
        return processed_data
    
    def buffer_to_numpy(self, buffer, width, height):
        """Convert GIMP buffer to numpy array"""
        # Get format info
        format = buffer.get_format()
        bpp = format.get_bytes_per_pixel()
        
        # Read pixel data
        rect = Gegl.Rectangle.new(0, 0, width, height)
        data = buffer.get(rect, 1.0, format, Gegl.AbyssPolicy.NONE)
        
        # Convert to numpy
        if bpp == 4:  # RGBA
            array = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 4)
            # Drop alpha channel for RGB
            rgb_array = array[:, :, :3]
        elif bpp == 3:  # RGB
            rgb_array = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
        else:
            # Convert grayscale to RGB
            gray = np.frombuffer(data, dtype=np.uint8).reshape(height, width)
            rgb_array = np.stack([gray, gray, gray], axis=2)
        
        return rgb_array
    
    def rgb_to_lab(self, rgb_array):
        """Convert RGB to LAB color space"""
        # Import color conversion (existing code)
        from analyze.color_conversion import convert_image_to_lab
        return convert_image_to_lab(rgb_array)
    
    def store_analysis_results(self, image, analysis_model):
        """Store analysis in GIMP image parasite"""
        import json
        
        # Serialize analysis results
        data = json.dumps(analysis_model.to_dict())
        
        # Create parasite (GIMP's metadata storage)
        parasite = Gimp.Parasite.new(
            "ai-separation-analysis",
            Gimp.ParasiteFlags.PERSISTENT,
            data.encode('utf-8')
        )
        
        # Attach to image
        image.attach_parasite(parasite)

Gimp.main(AnalyzePlugin.__gtype__, sys.argv)
```

## Data Flow in GIMP Context

### Input Flow
```
User opens image in GIMP
    ↓
User selects: Filters → AI Separation → Analyze Image
    ↓
Plugin extracts pixel data from active layer
    ↓
Converts to ProcessedImageData structure
    ↓
Runs existing analysis pipeline
```

### Output Storage
```
Analysis complete
    ↓
Results stored as GIMP parasite (metadata)
    ↓
Available for Color Match step
    ↓
User sees: "Analysis complete" message
```

## Key Implementation Details

### 1. No File Loading
- GIMP handles all file I/O
- Plugin works with already-loaded images
- No LOAD unit needed

### 2. Parasite Storage
- GIMP parasites = persistent metadata
- Survives save/load cycles
- Perfect for passing data between plugin steps

### 3. Silent Processing
- Maintains v1.1 behavior: no progress bars
- Only shows completion message
- Runs in main thread (GIMP handles responsiveness)

### 4. Multi-Resolution Strategy
```python
def create_resolutions(self, rgb_array):
    """Generate multi-resolution versions"""
    height, width = rgb_array.shape[:2]
    
    # Full resolution for color analysis
    full = rgb_array
    
    # Medium resolution for edge/texture (max 1000px wide)
    if width > 1000:
        scale = 1000 / width
        new_height = int(height * scale)
        medium = cv2.resize(rgb_array, (1000, new_height))
    else:
        medium = full
    
    return full, medium
```

### 5. Caching Integration
```python
# Use GIMP config directory for cache
cache_dir = os.path.join(
    GLib.get_user_config_dir(),
    'GIMP', '3.0', 'ai-separation-cache'
)

# GlobalState adapted to use this directory
global_state = GlobalState(cache_dir=cache_dir)
```

## Dependencies Bundling

### Required Libraries
```
analyze/
├── deps/
│   ├── numpy/          # Essential
│   ├── scipy/          # For KMeans, signal processing
│   ├── cv2/            # OpenCV for edge detection
│   ├── skimage/        # For texture analysis
│   └── colour_science/ # For LAB conversion
```

### Installation Script
```bash
#!/bin/bash
# bundle_deps.sh - Bundle dependencies with plugin

PLUGIN_DIR="gimp-ai-separation/analyze"
DEPS_DIR="$PLUGIN_DIR/deps"

mkdir -p $DEPS_DIR

# Install dependencies to plugin directory
pip install --target $DEPS_DIR \
    numpy==1.24.0 \
    scipy==1.10.0 \
    opencv-python==4.8.0 \
    scikit-image==0.21.0 \
    colour-science==0.4.3

# Remove unnecessary files to reduce size
find $DEPS_DIR -name "*.pyc" -delete
find $DEPS_DIR -name "__pycache__" -type d -delete
find $DEPS_DIR -name "tests" -type d -exec rm -rf {} +
```

## Performance Considerations

### GIMP-Specific Optimizations
1. **Layer vs. Image**: Analyze active layer only (faster)
2. **Preview Size**: Use GIMP's preview size for initial analysis
3. **Incremental Updates**: Support re-analysis without full recalc
4. **Memory Management**: Let GIMP handle large image tiling

### Timing Estimates
| Image Size | Standalone v1.1 | GIMP Plugin | Notes |
|------------|-----------------|-------------|-------|
| 1000×1000  | 10-15 sec      | 8-12 sec    | No file I/O overhead |
| 4000×3000  | 20-30 sec      | 18-25 sec   | GIMP's optimized buffers |
| 8000×6000  | 45-60 sec      | 40-50 sec   | Tiled processing |

## Error Handling

### GIMP-Friendly Errors
```python
def safe_analyze(self, image_data):
    """Wrap analysis with GIMP-appropriate error handling"""
    try:
        return self.analyze_internal(image_data)
    except MemoryError:
        Gimp.message("Image too large. Try reducing size first.")
        return None
    except ImportError as e:
        Gimp.message(f"Missing dependency: {e}. Please reinstall plugin.")
        return None
    except Exception as e:
        # Log to GIMP error console
        Gimp.message(f"Analysis error: {e}")
        # Also log details for debugging
        print(f"Detailed error: {traceback.format_exc()}")
        return None
```

## Testing in GIMP

### Manual Test Procedure
1. Copy plugin to GIMP plugins directory
2. Restart GIMP (or refresh plugins)
3. Open test image
4. Run: Filters → AI Separation → Analyze Image
5. Verify parasite attachment: Image → Image Properties → Parasites
6. Check cache creation in config directory

### Automated Testing
```python
# test_analyze_gimp.py - Run from GIMP Python console

def test_analyze():
    """Test analysis within GIMP"""
    image = Gimp.image_list()[0]  # Get first open image
    drawable = image.get_active_layer()
    
    # Create plugin instance
    plugin = AnalyzePlugin()
    
    # Extract data
    data = plugin.extract_image_data(image, drawable)
    assert data.rgb_image.shape[2] == 3
    
    # Run analysis
    analyzer = AnalyzeUnitCoordinator()
    result = analyzer.process(data)
    
    assert result.color_analysis is not None
    print("✓ Analysis successful")
    
test_analyze()
```

## Migration Path from Standalone

### Code Reuse Strategy
| Component | Changes Required | Effort |
|-----------|-----------------|---------|
| analyze_unit.py | None | 0% |
| color_analysis.py | None | 0% |
| edge_analysis.py | None | 0% |
| texture_analysis.py | None | 0% |
| data_structures.py | None | 0% |
| **NEW: analyze_plugin.py** | Create GIMP wrapper | 200 lines |

**Total effort: ~2-3 days** to fully integrate

## Next Steps

After review and approval of this specification:
1. Create Color Match module specification (adapts UI to GTK)
2. Create Separation module specification (outputs as GIMP layers)
3. Package complete plugin with installer
4. Create user documentation

## Summary

The Analyze module adapts cleanly to GIMP with minimal changes:
- ✅ 95% code reuse from existing v1.1
- ✅ No UI changes needed (already silent)
- ✅ Efficient GIMP buffer integration
- ✅ Parasite storage for data passing
- ✅ Maintains all analysis quality

Ready for implementation after review.