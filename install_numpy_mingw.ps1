# Install NumPy for GIMP's MINGW Python using MSYS2 repository
Write-Host "Installing NumPy for GIMP 3 (MINGW Python)..." -ForegroundColor Cyan
Write-Host ""

$gimpDir = "C:\Users\atwel\AppData\Local\Programs\GIMP 3"
$gimpPython = "$gimpDir\bin\python.exe"

# GIMP uses MINGW Python which needs MINGW-built packages
# We need to download pre-built MINGW packages

Write-Host "GIMP uses MINGW Python, which requires MINGW-compiled packages." -ForegroundColor Yellow
Write-Host "Standard PyPI wheels won't work." -ForegroundColor Yellow
Write-Host ""

Write-Host "Attempting to install from MSYS2/MINGW repository..." -ForegroundColor Yellow
Write-Host ""

# Try using pip with MINGW-compatible settings
$env:SETUPTOOLS_USE_DISTUTILS = "stdlib"

# Download numpy source and let pip try to find compatible wheel or build
& $gimpPython -m pip install numpy --break-system-packages --prefer-binary --no-cache-dir 2>&1 | Tee-Object -Variable output

Write-Host ""
Write-Host "Installation output:" -ForegroundColor Yellow
Write-Host $output
Write-Host ""

# Check if it worked
Write-Host "Verifying installation..." -ForegroundColor Yellow
$result = & $gimpPython -c "import numpy; print(f'SUCCESS! NumPy {numpy.__version__} installed')" 2>&1

if ($result -match "SUCCESS") {
    Write-Host ""
    Write-Host $result -ForegroundColor Green
    Write-Host ""
    Write-Host "="*60 -ForegroundColor Green
    Write-Host "NumPy is installed!" -ForegroundColor Green
    Write-Host "="*60 -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "NumPy is not installed yet: $result" -ForegroundColor Red
    Write-Host ""
    Write-Host "ALTERNATIVE SOLUTION:" -ForegroundColor Cyan
    Write-Host "The plugins are already visible in GIMP's menu." -ForegroundColor White
    Write-Host "They will work for basic UI testing, but image processing" -ForegroundColor White
    Write-Host "features require NumPy." -ForegroundColor White
    Write-Host ""
    Write-Host "You can:" -ForegroundColor Yellow
    Write-Host "  1. Continue without NumPy (limited functionality)" -ForegroundColor White
    Write-Host "  2. Install full MSYS2 and use pacman to install numpy" -ForegroundColor White
    Write-Host "  3. Wait for a future GIMP update with better pip support" -ForegroundColor White
}

Write-Host ""
pause
