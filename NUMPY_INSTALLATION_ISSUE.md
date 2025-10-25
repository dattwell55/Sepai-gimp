# NumPy Installation Issue for GIMP 3

## Problem Summary

The AI Separation plugins require NumPy, but installing NumPy for GIMP 3's Python environment on Windows is extremely challenging due to platform incompatibility issues.

## Root Cause

GIMP 3's Windows distribution uses a custom Python build with a very specific platform tag:
- **GIMP Python Platform**: `mingw_x86_64_ucrt_llvm`
- This means: MINGW64 toolchain + UCRT (Universal C Runtime) + LLVM/Clang compiler

## Attempted Solutions (All Failed)

### 1. pip install numpy
- **Failed**: No pip module available in GIMP's Python

### 2. Install pip and then numpy
- **Failed**: externally-managed-environment error
- Using `--break-system-packages` flag also failed

### 3. Download pre-built wheel from PyPI
- **Failed**: PyPI only has wheels for `win_amd64` (standard Windows Python)
- No `mingw_x86_64_ucrt_llvm` wheels available

### 4. Install from MSYS2 MINGW64
- **Failed**: MSYS2 MINGW64 provides `mingw_x86_64_msvcrt_gnu`
- Incompatible: uses MSVCRT instead of UCRT, and GCC instead of LLVM

### 5. Install from MSYS2 UCRT64
- **Failed**: MSYS2 UCRT64 provides `mingw_x86_64_ucrt_gnu`
- Incompatible: uses GCC instead of LLVM
- Even though both use UCRT, the compiler difference creates ABI incompatibility

## Platform Tag Comparison

| Source | Platform Tag | UCRT | Compiler | Compatible? |
|--------|-------------|------|----------|-------------|
| GIMP 3 Python | mingw_x86_64_ucrt_llvm | ✓ | LLVM/Clang | - |
| PyPI Wheels | win_amd64 | ✓ | MSVC | ✗ |
| MSYS2 MINGW64 | mingw_x86_64_msvcrt_gnu | ✗ | GCC | ✗ |
| MSYS2 UCRT64 | mingw_x86_64_ucrt_gnu | ✓ | GCC | ✗ |

## Why This Matters

NumPy contains compiled C extensions (.pyd files on Windows). These extensions must be compiled with the exact same toolchain (runtime library + compiler) as the Python interpreter. Mixing different compilers or runtimes causes module loading failures.

## Current Error

When trying to import NumPy:
```
ModuleNotFoundError: No module named 'numpy._core._multiarray_umath'
```

This happens because the `.pyd` file was compiled with a different toolchain than GIMP's Python expects.

## Possible Solutions (Not Yet Attempted)

### Option 1: Build NumPy from Source with LLVM
- **Complexity**: Very high
- **Requirements**:
  - Install LLVM/Clang compiler
  - Set up UCRT environment
  - Build NumPy from source with specific compiler flags
- **Time**: Hours to days
- **Risk**: May still fail due to dependency issues

### Option 2: Use Pure Python Implementation
- **Complexity**: Medium
- **Approach**: Rewrite plugins to avoid NumPy, using only Python standard library
- **Performance**: Much slower for image processing
- **Feasibility**: Possible for basic operations, but complex algorithms would be very slow

### Option 3: Contact GIMP/NumPy Communities
- Ask GIMP developers if they have NumPy packages for their Python build
- Ask if there's a LLVM-compiled NumPy wheel somewhere
- Check if GIMP developers plan to provide common packages

### Option 4: Switch to Linux or macOS
- NumPy installation is much simpler on these platforms
- GIMP's Python environment is more standard

## Current Workaround

The plugins have been modified to make NumPy optional:
```python
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: NumPy not available. Some features will be limited.")
```

This allows the plugins to load and show in GIMP's menu, but they cannot perform actual image processing without NumPy.

## Recommendation

**For now**: Accept that NumPy cannot be easily installed on this platform. The best path forward is likely:

1. **Short term**: Document this limitation and inform users that full functionality requires a different platform
2. **Medium term**: Consider rewriting critical parts to work without NumPy (though performance will suffer)
3. **Long term**: Either:
   - Build a custom LLVM-compiled NumPy wheel (very complex)
   - Wait for GIMP to provide NumPy in their distribution
   - Recommend users use Linux/macOS for this plugin

## Files Created During Installation Attempts

- `install_numpy_for_gimp.bat` - Basic pip install attempt
- `install_numpy_manual.ps1` - Manual pip installation with get-pip.py
- `install_numpy_direct.ps1` - Direct installation with --break-system-packages
- `install_numpy_wheel.ps1` - Download and install pre-built wheel
- `install_numpy_pacman.bat` - Attempt to use pacman from GIMP
- `install_numpy_msys2.md` - Instructions for MSYS2 installation
- `install_numpy_from_msys2.ps1` - MSYS2 MINGW64 installation script
- `copy_numpy_dlls.ps1` - Copy DLL dependencies
- `install_numpy_ucrt.ps1` - MSYS2 UCRT64 installation script

All of these approaches failed due to platform incompatibility.

## Status

**NumPy Installation**: BLOCKED - Platform incompatibility
**Plugin Functionality**: LIMITED - Plugins load but cannot process images
**Next Steps**: Decide between building from source, rewriting without NumPy, or accepting limitation
