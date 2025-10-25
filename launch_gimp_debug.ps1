# PowerShell script to launch GIMP with debug output
Write-Host "Looking for GIMP installation..." -ForegroundColor Yellow

$gimpPaths = @(
    "C:\Program Files\GIMP 3\bin\gimp-3.0.exe",
    "C:\Program Files (x86)\GIMP 3\bin\gimp-3.0.exe",
    "C:\Program Files\GIMP 2.99\bin\gimp-2.99.exe",
    "C:\msys64\mingw64\bin\gimp-3.0.exe"
)

$gimpExe = $null
foreach ($path in $gimpPaths) {
    if (Test-Path $path) {
        $gimpExe = $path
        break
    }
}

if (-not $gimpExe) {
    Write-Host "ERROR: Could not find GIMP executable" -ForegroundColor Red
    Write-Host "Searched locations:" -ForegroundColor Yellow
    foreach ($path in $gimpPaths) {
        Write-Host "  - $path"
    }
    Write-Host ""
    Write-Host "Please find gimp-3.0.exe on your system and run:" -ForegroundColor Yellow
    Write-Host '  & "C:\Path\To\gimp-3.0.exe" --verbose --console-messages'
    pause
    exit 1
}

Write-Host "Found GIMP at: $gimpExe" -ForegroundColor Green
Write-Host ""
Write-Host "Starting GIMP with console output..." -ForegroundColor Cyan
Write-Host "Look for any Python errors or AI Separation plugin messages" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop GIMP when done" -ForegroundColor Yellow
Write-Host ""

& $gimpExe --verbose --console-messages

Write-Host ""
Write-Host "GIMP closed. Press any key to exit..." -ForegroundColor Yellow
pause
