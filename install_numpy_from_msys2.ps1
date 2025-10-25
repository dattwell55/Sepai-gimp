# Complete NumPy Installation from MSYS2 to GIMP
Write-Host "Installing NumPy for GIMP 3 from MSYS2..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if MSYS2 is installed
$msys2Path = "C:\msys64"
if (-not (Test-Path $msys2Path)) {
    Write-Host "ERROR: MSYS2 not found at C:\msys64" -ForegroundColor Red
    Write-Host "Please make sure MSYS2 is installed at the default location." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Found MSYS2 at: $msys2Path" -ForegroundColor Green
Write-Host ""

# Step 2: Install NumPy in MSYS2
Write-Host "Step 1: Installing NumPy in MSYS2 MINGW64..." -ForegroundColor Yellow
Write-Host "  Running: pacman -S --noconfirm mingw-w64-x86_64-python-numpy" -ForegroundColor Cyan
Write-Host ""

$msys2Bash = "$msys2Path\usr\bin\bash.exe"
& $msys2Bash -lc "pacman -S --noconfirm mingw-w64-x86_64-python-numpy"

Write-Host ""
Write-Host "Checking MSYS2 NumPy installation..." -ForegroundColor Yellow
$msys2Check = & $msys2Bash -lc "python -c 'import numpy; print(numpy.__version__)'" 2>&1

if ($msys2Check -match '^\d+\.\d+') {
    Write-Host "  NumPy $msys2Check installed in MSYS2!" -ForegroundColor Green
} else {
    Write-Host "  Warning: Could not verify MSYS2 NumPy installation" -ForegroundColor Yellow
    Write-Host "  Output: $msys2Check" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Copy NumPy from MSYS2 to GIMP
Write-Host "Step 2: Copying NumPy from MSYS2 to GIMP..." -ForegroundColor Yellow

$msys2SitePackages = "$msys2Path\mingw64\lib\python3.12\site-packages"
$gimpSitePackages = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\lib\python3.12\site-packages"

# Check if source exists
if (-not (Test-Path "$msys2SitePackages\numpy")) {
    Write-Host "  ERROR: NumPy not found in MSYS2 at $msys2SitePackages\numpy" -ForegroundColor Red
    Write-Host "  Please install NumPy in MSYS2 manually first." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Check if destination exists
if (-not (Test-Path $gimpSitePackages)) {
    Write-Host "  ERROR: GIMP site-packages not found at $gimpSitePackages" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Copy numpy folder
Write-Host "  Copying numpy folder..." -ForegroundColor Cyan
Copy-Item -Path "$msys2SitePackages\numpy" -Destination "$gimpSitePackages\numpy" -Recurse -Force
Write-Host "    Done!" -ForegroundColor Green

# Copy numpy dist-info
Write-Host "  Copying numpy dist-info..." -ForegroundColor Cyan
$distInfo = Get-ChildItem "$msys2SitePackages\numpy-*.dist-info" | Select-Object -First 1
if ($distInfo) {
    Copy-Item -Path $distInfo.FullName -Destination "$gimpSitePackages\$($distInfo.Name)" -Recurse -Force
    Write-Host "    Done! ($($distInfo.Name))" -ForegroundColor Green
} else {
    Write-Host "    Warning: No dist-info found" -ForegroundColor Yellow
}

# Copy numpy.libs if it exists
if (Test-Path "$msys2SitePackages\numpy.libs") {
    Write-Host "  Copying numpy.libs folder..." -ForegroundColor Cyan
    Copy-Item -Path "$msys2SitePackages\numpy.libs" -Destination "$gimpSitePackages\numpy.libs" -Recurse -Force
    Write-Host "    Done!" -ForegroundColor Green
}

Write-Host ""

# Step 4: Verify installation in GIMP Python
Write-Host "Step 3: Verifying NumPy in GIMP Python..." -ForegroundColor Yellow

$gimpPython = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe"
$verifyResult = & $gimpPython -c "import numpy; print('NumPy', numpy.__version__, 'installed!')" 2>&1

if ($verifyResult -match "NumPy.*installed") {
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
    Write-Host "Installation check failed:" -ForegroundColor Red
    Write-Host "  $verifyResult" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the errors above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
