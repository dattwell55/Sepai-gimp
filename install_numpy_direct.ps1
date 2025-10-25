# Install NumPy directly into GIMP's Python site-packages
Write-Host "Installing NumPy for GIMP 3 Python (direct installation)..." -ForegroundColor Cyan
Write-Host ""

$gimpPython = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe"
$gimpSitePackages = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\lib\python3.11\site-packages"

# Check Python version
Write-Host "Checking GIMP Python version..." -ForegroundColor Yellow
$pythonVersion = & $gimpPython --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor Green
Write-Host ""

# Download get-pip.py with --break-system-packages support
Write-Host "Downloading get-pip.py..." -ForegroundColor Yellow
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$getPipPath = "$env:TEMP\get-pip.py"
Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath
Write-Host "  Downloaded to $getPipPath" -ForegroundColor Green
Write-Host ""

# Install pip with --break-system-packages
Write-Host "Installing pip (with --break-system-packages)..." -ForegroundColor Yellow
& $gimpPython $getPipPath --break-system-packages
Write-Host ""

# Install numpy
Write-Host "Installing numpy (with --break-system-packages)..." -ForegroundColor Yellow
& $gimpPython -m pip install numpy --break-system-packages
Write-Host ""

# Verify installation
Write-Host "Verifying NumPy installation..." -ForegroundColor Yellow
$testResult = & $gimpPython -c "import numpy; print(f'NumPy {numpy.__version__} installed successfully!')" 2>&1

if ($testResult -match "successfully") {
    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host $testResult -ForegroundColor Green
    Write-Host ""
    Write-Host "Now:" -ForegroundColor Cyan
    Write-Host "  1. Restart GIMP" -ForegroundColor White
    Write-Host "  2. Open an image" -ForegroundColor White
    Write-Host "  3. Run: Filters -> Render -> AI Separation: Analyze Image (Step 1)" -ForegroundColor White
    Write-Host "  4. The plugin should now work!" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Installation check result:" -ForegroundColor Yellow
    Write-Host $testResult
    Write-Host ""
    Write-Host "There may have been an error. Check the output above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
