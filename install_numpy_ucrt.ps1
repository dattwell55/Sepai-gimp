# Install NumPy for GIMP 3 from MSYS2 UCRT64 environment
Write-Host "Installing NumPy for GIMP 3 from MSYS2 UCRT64..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Install NumPy in MSYS2 UCRT64
Write-Host "Step 1: Installing NumPy in MSYS2 UCRT64..." -ForegroundColor Yellow
Write-Host "  Running: pacman -S --noconfirm mingw-w64-ucrt-x86_64-python-numpy" -ForegroundColor Cyan
Write-Host ""

$msys2Bash = "C:\msys64\usr\bin\bash.exe"
& $msys2Bash -lc "pacman -S --noconfirm mingw-w64-ucrt-x86_64-python-numpy"

Write-Host ""
Write-Host "Checking MSYS2 UCRT64 NumPy installation..." -ForegroundColor Yellow
$msys2Check = & $msys2Bash -lc "MSYSTEM=UCRT64 /ucrt64/bin/python -c 'import numpy; print(numpy.__version__)'" 2>&1

if ($msys2Check -match '^\d+\.\d+') {
    Write-Host "  NumPy $msys2Check installed in MSYS2 UCRT64!" -ForegroundColor Green
} else {
    Write-Host "  Warning: Could not verify MSYS2 UCRT64 NumPy installation" -ForegroundColor Yellow
    Write-Host "  Output: $msys2Check" -ForegroundColor Gray
}

Write-Host ""

# Step 2: Clean old MINGW64 numpy from GIMP
Write-Host "Step 2: Removing old NumPy installation..." -ForegroundColor Yellow
$gimpSitePackages = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\lib\python3.12\site-packages"

if (Test-Path "$gimpSitePackages\numpy") {
    Write-Host "  Removing old numpy folder..." -ForegroundColor Cyan
    Remove-Item -Path "$gimpSitePackages\numpy" -Recurse -Force
    Write-Host "    Done!" -ForegroundColor Green
}

if (Test-Path "$gimpSitePackages\numpy*.dist-info") {
    Write-Host "  Removing old numpy dist-info..." -ForegroundColor Cyan
    Remove-Item -Path "$gimpSitePackages\numpy*.dist-info" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "    Done!" -ForegroundColor Green
}

if (Test-Path "$gimpSitePackages\numpy.libs") {
    Write-Host "  Removing old numpy.libs..." -ForegroundColor Cyan
    Remove-Item -Path "$gimpSitePackages\numpy.libs" -Recurse -Force
    Write-Host "    Done!" -ForegroundColor Green
}

Write-Host ""

# Step 3: Copy NumPy from MSYS2 UCRT64 to GIMP
Write-Host "Step 3: Copying NumPy from MSYS2 UCRT64 to GIMP..." -ForegroundColor Yellow

$ucrtSitePackages = "C:\msys64\ucrt64\lib\python3.12\site-packages"

# Check if source exists
if (-not (Test-Path "$ucrtSitePackages\numpy")) {
    Write-Host "  ERROR: NumPy not found in MSYS2 UCRT64 at $ucrtSitePackages\numpy" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Copy numpy folder
Write-Host "  Copying numpy folder..." -ForegroundColor Cyan
Copy-Item -Path "$ucrtSitePackages\numpy" -Destination "$gimpSitePackages\numpy" -Recurse -Force
Write-Host "    Done!" -ForegroundColor Green

# Copy numpy dist-info
Write-Host "  Copying numpy dist-info..." -ForegroundColor Cyan
$distInfo = Get-ChildItem "$ucrtSitePackages\numpy-*.dist-info" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($distInfo) {
    Copy-Item -Path $distInfo.FullName -Destination "$gimpSitePackages\$($distInfo.Name)" -Recurse -Force
    Write-Host "    Done! ($($distInfo.Name))" -ForegroundColor Green
} else {
    Write-Host "    Warning: No dist-info found" -ForegroundColor Yellow
}

# Copy numpy.libs if it exists
if (Test-Path "$ucrtSitePackages\numpy.libs") {
    Write-Host "  Copying numpy.libs folder..." -ForegroundColor Cyan
    Copy-Item -Path "$ucrtSitePackages\numpy.libs" -Destination "$gimpSitePackages\numpy.libs" -Recurse -Force
    Write-Host "    Done!" -ForegroundColor Green
}

Write-Host ""

# Step 4: Copy required DLLs from UCRT64
Write-Host "Step 4: Copying required DLLs from MSYS2 UCRT64..." -ForegroundColor Yellow

$ucrtBin = "C:\msys64\ucrt64\bin"
$gimpBin = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin"

$requiredDlls = @(
    "libopenblas*.dll",
    "libgfortran*.dll",
    "libquadmath*.dll",
    "libgcc_s*.dll"
)

$copiedCount = 0
foreach ($dllPattern in $requiredDlls) {
    $dlls = Get-ChildItem -Path $ucrtBin -Filter $dllPattern -ErrorAction SilentlyContinue

    if ($dlls) {
        foreach ($dll in $dlls) {
            $destPath = Join-Path $gimpBin $dll.Name

            if (Test-Path $destPath) {
                Write-Host "  $($dll.Name) - already exists" -ForegroundColor Gray
            } else {
                Write-Host "  Copying $($dll.Name)..." -ForegroundColor Cyan
                Copy-Item -Path $dll.FullName -Destination $destPath -Force
                Write-Host "    Done!" -ForegroundColor Green
                $copiedCount++
            }
        }
    }
}

Write-Host "  Copied $copiedCount new DLL(s)" -ForegroundColor Green
Write-Host ""

# Step 5: Verify installation in GIMP Python
Write-Host "Step 5: Verifying NumPy in GIMP Python..." -ForegroundColor Yellow

$gimpPython = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe"
$verifyResult = & $gimpPython -c "import numpy; print('NumPy', numpy.__version__, 'installed successfully!')" 2>&1

if ($verifyResult -match "installed successfully") {
    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "  $verifyResult" -ForegroundColor Green
    Write-Host ""
    Write-Host "Let's also check the platform tag..." -ForegroundColor Cyan

    # Check platform tag of installed numpy
    $platformCheck = powershell.exe -Command "Get-ChildItem '$gimpSitePackages\numpy\_core' -Filter '*multiarray_umath*.pyd' | Select-Object -First 1 | ForEach-Object { `$_.Name }"
    Write-Host "  Installed .pyd file: $platformCheck" -ForegroundColor White

    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Close GIMP completely (if running)" -ForegroundColor White
    Write-Host "  2. Restart GIMP" -ForegroundColor White
    Write-Host "  3. Open an image" -ForegroundColor White
    Write-Host "  4. Run: Filters -> Render -> AI Separation: Analyze Image (Step 1)" -ForegroundColor White
    Write-Host "  5. The plugin should now work with full functionality!" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "NumPy installation verification failed:" -ForegroundColor Red
    Write-Host "$verifyResult" -ForegroundColor Gray
    Write-Host ""

    # Check platform tag mismatch
    Write-Host "Checking platform tag compatibility..." -ForegroundColor Yellow
    $gimpPlatform = & $gimpPython -c "import sysconfig; print(sysconfig.get_platform())" 2>&1
    Write-Host "  GIMP Python platform: $gimpPlatform" -ForegroundColor White

    $numpyPyd = powershell.exe -Command "Get-ChildItem '$gimpSitePackages\numpy\_core' -Filter '*multiarray_umath*.pyd' -ErrorAction SilentlyContinue | Select-Object -First 1 | ForEach-Object { `$_.Name }"
    if ($numpyPyd) {
        Write-Host "  NumPy .pyd file: $numpyPyd" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
