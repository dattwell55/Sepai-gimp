@echo off
echo Installing NumPy for GIMP 3 using MSYS2 pacman...
echo.

REM GIMP uses MSYS2, so we need to use pacman to install packages
set PACMAN="C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\pacman.exe"

if not exist %PACMAN% (
    echo ERROR: Could not find pacman at %PACMAN%
    echo GIMP installation may be different than expected
    pause
    exit /b 1
)

echo Found pacman at: %PACMAN%
echo.
echo Installing mingw-w64-x86_64-python-numpy...
echo.

%PACMAN% -S --noconfirm mingw-w64-x86_64-python-numpy

echo.
echo Verifying installation...
"C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe" -c "import numpy; print('NumPy version:', numpy.__version__)"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! NumPy is installed!
    echo.
    echo Now restart GIMP and check Filters -^> Render for AI Separation plugins
) else (
    echo.
    echo NumPy installation may have failed. Check errors above.
)

echo.
pause
