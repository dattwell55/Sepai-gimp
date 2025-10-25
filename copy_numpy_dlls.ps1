# Copy NumPy DLL dependencies from MSYS2 to GIMP
Write-Host "Copying NumPy DLL dependencies from MSYS2 to GIMP..." -ForegroundColor Cyan
Write-Host ""

$msys2Bin = "C:\msys64\mingw64\bin"
$gimpBin = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin"

# List of DLLs that NumPy depends on
$requiredDlls = @(
    "libopenblas*.dll",
    "libgfortran*.dll",
    "libquadmath*.dll",
    "libgcc_s*.dll",
    "libwinpthread*.dll"
)

Write-Host "Searching for required DLLs in MSYS2..." -ForegroundColor Yellow
$copiedCount = 0

foreach ($dllPattern in $requiredDlls) {
    $dlls = Get-ChildItem -Path $msys2Bin -Filter $dllPattern -ErrorAction SilentlyContinue

    if ($dlls) {
        foreach ($dll in $dlls) {
            $destPath = Join-Path $gimpBin $dll.Name

            # Check if already exists
            if (Test-Path $destPath) {
                Write-Host "  $($dll.Name) - already exists" -ForegroundColor Gray
            } else {
                Write-Host "  Copying $($dll.Name)..." -ForegroundColor Cyan
                Copy-Item -Path $dll.FullName -Destination $destPath -Force
                Write-Host "    Done!" -ForegroundColor Green
                $copiedCount++
            }
        }
    } else {
        Write-Host "  Warning: No DLLs matching $dllPattern found" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Copied $copiedCount new DLL(s)" -ForegroundColor Green
Write-Host ""

# Verify NumPy installation
Write-Host "Verifying NumPy installation in GIMP Python..." -ForegroundColor Yellow
$gimpPython = "$gimpBin\python.exe"
$verifyResult = & $gimpPython -c "import numpy; print('NumPy', numpy.__version__, 'installed successfully!')" 2>&1

if ($verifyResult -match "installed successfully") {
    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "  $verifyResult" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Close GIMP completely (if running)" -ForegroundColor White
    Write-Host "  2. Restart GIMP" -ForegroundColor White
    Write-Host "  3. Open an image" -ForegroundColor White
    Write-Host "  4. Run: Filters -> Render -> AI Separation: Analyze Image (Step 1)" -ForegroundColor White
    Write-Host "  5. The plugin should now work with full functionality!" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "NumPy still cannot be imported:" -ForegroundColor Red
    Write-Host "$verifyResult" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Trying to find missing DLLs..." -ForegroundColor Yellow

    # Try to get more detailed error
    $detailError = & $gimpPython -c "import sys; sys.path.insert(0, 'C:/Users/atwel/AppData/Local/Programs/GIMP 3/lib/python3.12/site-packages'); import numpy" 2>&1
    Write-Host "$detailError" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
