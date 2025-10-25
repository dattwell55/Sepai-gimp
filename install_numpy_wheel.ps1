# Install NumPy pre-built wheel for GIMP 3 Python
Write-Host "Installing NumPy (pre-built wheel) for GIMP 3 Python..." -ForegroundColor Cyan
Write-Host ""

$gimpPython = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe"

# Check Python version details
Write-Host "Checking Python details..." -ForegroundColor Yellow
$pythonVersion = & $gimpPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$pythonArch = & $gimpPython -c "import platform; print(platform.machine())"
Write-Host "  Python version: $pythonVersion" -ForegroundColor Green
Write-Host "  Architecture: $pythonArch" -ForegroundColor Green
Write-Host ""

# Determine the correct wheel
# Python 3.12 on AMD64 (x86_64) Windows
$numpyWheel = "numpy-2.1.3-cp312-cp312-win_amd64.whl"
$downloadUrl = "https://files.pythonhosted.org/packages/4b/d7/ecf66c1cd12dc28fb4b5c8eac8a081f7fbd6ff66b9ddbef4c68c3c75d2d4/$numpyWheel"

Write-Host "Downloading NumPy pre-built wheel..." -ForegroundColor Yellow
Write-Host "  URL: $downloadUrl" -ForegroundColor Gray

$wheelPath = "$env:TEMP\$numpyWheel"

try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $wheelPath
    Write-Host "  Downloaded to: $wheelPath" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "  Failed to download. Trying alternative..." -ForegroundColor Yellow
    # Try numpy 2.0.2 which is known to have pre-built wheels
    $numpyWheel = "numpy-2.0.2-cp312-cp312-win_amd64.whl"
    $downloadUrl = "https://files.pythonhosted.org/packages/4a/d9/32f8a2e1298a0dcd8b869c80eb5e5f1ebd8e36918e5e71d13f2685c8e26e/$numpyWheel"
    $wheelPath = "$env:TEMP\$numpyWheel"

    Invoke-WebRequest -Uri $downloadUrl -OutFile $wheelPath
    Write-Host "  Downloaded to: $wheelPath" -ForegroundColor Green
    Write-Host ""
}

# Install the wheel
Write-Host "Installing NumPy wheel..." -ForegroundColor Yellow
& $gimpPython -m pip install --break-system-packages --no-deps $wheelPath
Write-Host ""

# Verify installation
Write-Host "Verifying NumPy installation..." -ForegroundColor Yellow
$testResult = & $gimpPython -c "import numpy; print(f'SUCCESS! NumPy {numpy.__version__} installed')" 2>&1

if ($testResult -match "SUCCESS") {
    Write-Host ""
    Write-Host $testResult -ForegroundColor Green
    Write-Host ""
    Write-Host "NumPy is now installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Restart GIMP completely" -ForegroundColor White
    Write-Host "  2. Open an image in GIMP" -ForegroundColor White
    Write-Host "  3. Go to: Filters -> Render -> AI Separation: Analyze Image (Step 1)" -ForegroundColor White
    Write-Host "  4. The plugin should now work with full functionality!" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Verification result:" -ForegroundColor Yellow
    Write-Host $testResult
    Write-Host ""
    Write-Host "Installation may have failed. Check errors above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
