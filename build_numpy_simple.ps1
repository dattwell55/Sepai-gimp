# Simpler NumPy build script
Write-Host "Building NumPy with LLVM in MSYS2 UCRT64..." -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Downloading NumPy source..." -ForegroundColor Yellow
& "C:\msys64\usr\bin\bash.exe" -lc @"
export MSYSTEM=UCRT64
cd /tmp
rm -rf numpy-build
mkdir numpy-build
cd numpy-build
/ucrt64/bin/python -m pip download --no-binary numpy --no-deps numpy
echo "Download complete"
ls -la *.tar.gz
"@

Write-Host ""
Write-Host "Step 2: Extracting source..." -ForegroundColor Yellow
& "C:\msys64\usr\bin\bash.exe" -lc @"
export MSYSTEM=UCRT64
cd /tmp/numpy-build
tar -xzf numpy-*.tar.gz
echo "Extracted to:"
ls -d numpy-*/
"@

Write-Host ""
Write-Host "Step 3: Installing build requirements..." -ForegroundColor Yellow
& "C:\msys64\usr\bin\bash.exe" -lc @"
export MSYSTEM=UCRT64
cd /tmp/numpy-build/numpy-*/
/ucrt64/bin/python -m pip install --upgrade pip setuptools wheel meson-python ninja cython
"@

Write-Host ""
Write-Host "Step 4: Building NumPy with Clang..." -ForegroundColor Yellow
Write-Host "  This will take 10-20 minutes..." -ForegroundColor Cyan
& "C:\msys64\usr\bin\bash.exe" -lc @"
export MSYSTEM=UCRT64
export CC=clang
export CXX=clang++
cd /tmp/numpy-build/numpy-*/
/ucrt64/bin/python -m pip wheel --no-build-isolation --no-deps -w /tmp .
echo "Build complete!"
ls -la /tmp/numpy-*.whl
"@

Write-Host ""
Write-Host "Step 5: Copying wheel to Windows..." -ForegroundColor Yellow
Copy-Item "C:\msys64\tmp\numpy-*.whl" -Destination "C:\Users\atwel\OneDrive\Documents\-SepAI-gimp-main\"

$wheel = Get-ChildItem "C:\Users\atwel\OneDrive\Documents\-SepAI-gimp-main" -Filter "numpy-*.whl" | Select-Object -First 1
if ($wheel) {
    Write-Host "  Wheel copied: $($wheel.Name)" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Wheel not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 6: Installing into GIMP Python..." -ForegroundColor Yellow
& "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe" -m pip install --force-reinstall "$($wheel.FullName)"

Write-Host ""
Write-Host "Step 7: Verifying..." -ForegroundColor Yellow
$result = & "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe" -c "import numpy; print('SUCCESS: NumPy', numpy.__version__)" 2>&1
Write-Host $result -ForegroundColor Green

Write-Host ""
Write-Host "Done! Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
