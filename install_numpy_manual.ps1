# Install NumPy for GIMP 3 manually
Write-Host "Installing NumPy for GIMP 3 Python..." -ForegroundColor Cyan

$gimpPython = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe"
$gimpLibDir = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\lib\python3.11\site-packages"

# Check if GIMP Python exists
if (-not (Test-Path $gimpPython)) {
    Write-Host "ERROR: GIMP Python not found at $gimpPython" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Found GIMP Python at: $gimpPython" -ForegroundColor Green
Write-Host ""

# First, try to install pip
Write-Host "Step 1: Installing pip..." -ForegroundColor Yellow
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$getPipPath = "$env:TEMP\get-pip.py"

try {
    Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath
    & $gimpPython $getPipPath
    Write-Host "pip installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Failed to install pip automatically" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 2: Installing numpy..." -ForegroundColor Yellow

# Try using pip if it's now available
& $gimpPython -m pip install numpy 2>&1 | Out-String

Write-Host ""
Write-Host "Checking numpy installation..." -ForegroundColor Yellow
$checkResult = & $gimpPython -c "import numpy; print('NumPy version:', numpy.__version__)" 2>&1

if ($checkResult -match "NumPy version") {
    Write-Host "SUCCESS! NumPy is installed: $checkResult" -ForegroundColor Green
    Write-Host ""
    Write-Host "Now restart GIMP and check Filters -> Render" -ForegroundColor Cyan
} else {
    Write-Host "NumPy installation may have failed" -ForegroundColor Red
    Write-Host "Error: $checkResult" -ForegroundColor Red
    Write-Host ""
    Write-Host "You may need to manually install NumPy" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
