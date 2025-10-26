# Build NumPy from source using MSYS2 UCRT64 LLVM toolchain for GIMP 3
Write-Host "Building NumPy from source with LLVM for GIMP 3..." -ForegroundColor Cyan
Write-Host ""

# Check for MSYS2 UCRT64
$msys2Path = "C:\msys64"
if (-not (Test-Path $msys2Path)) {
    Write-Host "ERROR: MSYS2 not found at $msys2Path" -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Found MSYS2 at: $msys2Path" -ForegroundColor Green
Write-Host ""

# Step 1: Install build dependencies
Write-Host "Step 1: Installing build dependencies in MSYS2 UCRT64..." -ForegroundColor Yellow
Write-Host "  This may take several minutes..." -ForegroundColor Cyan
Write-Host ""

$msys2Bash = "$msys2Path\usr\bin\bash.exe"

# Install required build tools and dependencies
Write-Host "  Installing compiler and build tools..." -ForegroundColor Cyan
& $msys2Bash -lc "pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-clang mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-pip mingw-w64-ucrt-x86_64-openblas mingw-w64-ucrt-x86_64-meson mingw-w64-ucrt-x86_64-ninja mingw-w64-ucrt-x86_64-cython mingw-w64-ucrt-x86_64-pkgconf"

Write-Host ""
Write-Host "  Build dependencies installed!" -ForegroundColor Green
Write-Host ""

# Step 2: Build NumPy using LLVM
Write-Host "Step 2: Building NumPy from source with LLVM/Clang..." -ForegroundColor Yellow
Write-Host "  This will take 10-20 minutes depending on your system..." -ForegroundColor Cyan
Write-Host ""

# Create a build script for MSYS2
$buildScript = @"
#!/bin/bash
set -e

# Set environment to use UCRT64
export MSYSTEM=UCRT64
source /etc/profile

# Set compilers to LLVM/Clang
export CC=clang
export CXX=clang++

# Create temp directory for build
BUILD_DIR=/tmp/numpy-build-gimp
rm -rf `$BUILD_DIR
mkdir -p `$BUILD_DIR
cd `$BUILD_DIR

# Download NumPy source
echo "Downloading NumPy source..."
/ucrt64/bin/python -m pip download --no-binary numpy --no-deps numpy

# Extract
tar -xzf numpy-*.tar.gz
cd numpy-*/

# Install build dependencies
echo "Installing Python build dependencies..."
/ucrt64/bin/python -m pip install --upgrade pip setuptools wheel
/ucrt64/bin/python -m pip install meson-python ninja cython

# Build NumPy with LLVM
echo "Building NumPy with Clang/LLVM..."
echo "This may take 10-20 minutes..."

# Create a meson cross-file to ensure LLVM is used
cat > llvm-cross.ini << EOF
[binaries]
c = 'clang'
cpp = 'clang++'
ar = 'llvm-ar'

[built-in options]
c_args = ['-DMS_WIN64']
cpp_args = ['-DMS_WIN64']

[host_machine]
system = 'windows'
cpu_family = 'x86_64'
cpu = 'x86_64'
endian = 'little'
EOF

# Build
/ucrt64/bin/python -m pip wheel --no-build-isolation --no-deps -w /tmp .

# Copy the wheel to a accessible location
cp /tmp/numpy-*.whl /c/Users/atwel/OneDrive/Documents/-SepAI-gimp-main/

echo "Build complete! Wheel saved to project directory."
"@

# Save the build script
$buildScriptPath = "$env:TEMP\build_numpy.sh"
$buildScript | Out-File -FilePath $buildScriptPath -Encoding ASCII

# Run the build script in MSYS2
& $msys2Bash -l $buildScriptPath

Write-Host ""
Write-Host "Step 3: Installing NumPy wheel into GIMP Python..." -ForegroundColor Yellow

# Find the built wheel
$wheel = Get-ChildItem "C:\Users\atwel\OneDrive\Documents\-SepAI-gimp-main" -Filter "numpy-*.whl" | Select-Object -First 1

if (-not $wheel) {
    Write-Host "  ERROR: NumPy wheel not found!" -ForegroundColor Red
    Write-Host "  Build may have failed. Check output above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "  Found wheel: $($wheel.Name)" -ForegroundColor Green
Write-Host "  Installing into GIMP Python..." -ForegroundColor Cyan

$gimpPython = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe"

# Install the wheel
& $gimpPython -m pip install --force-reinstall "$($wheel.FullName)" 2>&1

Write-Host ""
Write-Host "Step 4: Verifying installation..." -ForegroundColor Yellow

$verifyResult = & $gimpPython -c "import numpy; print('NumPy', numpy.__version__, 'installed successfully!')" 2>&1

if ($verifyResult -match "installed successfully") {
    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "  $verifyResult" -ForegroundColor Green
    Write-Host ""
    Write-Host "NumPy has been built with LLVM and installed for GIMP 3!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Close GIMP completely (if running)" -ForegroundColor White
    Write-Host "  2. Restart GIMP" -ForegroundColor White
    Write-Host "  3. Open an image" -ForegroundColor White
    Write-Host "  4. Run: Filters -> Render -> AI Separation: Analyze Image (Step 1)" -ForegroundColor White
    Write-Host "  5. The plugin should now work with full functionality!" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Installation verification failed:" -ForegroundColor Red
    Write-Host "$verifyResult" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
