# Download and install NumPy wheel directly
Write-Host "Installing NumPy for GIMP 3 Python (direct download)..." -ForegroundColor Cyan
Write-Host ""

$gimpPython = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe"

# Correct URL for NumPy 2.0.2 for Python 3.12 Windows AMD64
$wheelUrl = "https://pypi.org/simple/numpy/"
$wheelFile = "numpy-2.0.2-cp312-cp312-win_amd64.whl"
$wheelPath = "$env:TEMP\$wheelFile"

Write-Host "Step 1: Finding correct NumPy wheel URL..." -ForegroundColor Yellow

# Get the PyPI simple index page
$response = Invoke-WebRequest -Uri $wheelUrl -UseBasicParsing
$content = $response.Content

# Find the correct wheel URL
$pattern = 'href="([^"]*' + [regex]::Escape($wheelFile) + '[^"]*)"'
if ($content -match $pattern) {
    $actualUrl = $matches[1]
    # Remove the hash part if present
    $actualUrl = $actualUrl -replace '#.*$', ''

    Write-Host "  Found: $actualUrl" -ForegroundColor Green
    Write-Host ""

    Write-Host "Step 2: Downloading NumPy wheel..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $actualUrl -OutFile $wheelPath
    Write-Host "  Downloaded to: $wheelPath" -ForegroundColor Green
    Write-Host ""

    Write-Host "Step 3: Installing wheel..." -ForegroundColor Yellow
    & $gimpPython -m pip install --break-system-packages --force-reinstall $wheelPath
    Write-Host ""

    Write-Host "Step 4: Verifying installation..." -ForegroundColor Yellow
    $result = & $gimpPython -c "import numpy; print(f'SUCCESS! NumPy {numpy.__version__} installed')" 2>&1

    if ($result -match "SUCCESS") {
        Write-Host ""
        Write-Host $result -ForegroundColor Green
        Write-Host ""
        Write-Host "="*60 -ForegroundColor Green
        Write-Host "NumPy is now installed in GIMP Python!" -ForegroundColor Green
        Write-Host "="*60 -ForegroundColor Green
        Write-Host ""
        Write-Host "NEXT STEPS:" -ForegroundColor Cyan
        Write-Host "  1. Close GIMP completely (if running)" -ForegroundColor White
        Write-Host "  2. Restart GIMP" -ForegroundColor White
        Write-Host "  3. Open any image" -ForegroundColor White
        Write-Host "  4. Go to: Filters -> Render -> AI Separation: Analyze Image" -ForegroundColor White
        Write-Host "  5. The plugin should now work!" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "Verification failed: $result" -ForegroundColor Red
    }
} else {
    Write-Host "  Could not find wheel URL" -ForegroundColor Red
    Write-Host ""
    Write-Host "Trying alternative approach..." -ForegroundColor Yellow

    # Try installing using pip index directly
    & $gimpPython -m pip install --break-system-packages --index-url https://pypi.org/simple/ numpy==2.0.2

    Write-Host ""
    $result = & $gimpPython -c "import numpy; print(f'NumPy {numpy.__version__} installed')" 2>&1
    Write-Host "Result: $result"
}

Write-Host ""
pause
