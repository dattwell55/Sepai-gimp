# Simple NumPy installation using pip's built-in wheel finding
Write-Host "Installing NumPy for GIMP 3 Python..." -ForegroundColor Cyan
Write-Host ""

$gimpPython = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe"

Write-Host "Installing NumPy (pip will find the correct pre-built wheel)..." -ForegroundColor Yellow
& $gimpPython -m pip install numpy --break-system-packages --only-binary :all: --no-build-isolation

Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
$result = & $gimpPython -c "import numpy; print(f'SUCCESS! NumPy {numpy.__version__} installed')" 2>&1

if ($result -match "SUCCESS") {
    Write-Host ""
    Write-Host $result -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. RESTART GIMP completely" -ForegroundColor White
    Write-Host "  2. Open an image" -ForegroundColor White
    Write-Host "  3. Try: Filters -> Render -> AI Separation: Analyze Image" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Result: $result" -ForegroundColor Yellow
}

Write-Host ""
pause
