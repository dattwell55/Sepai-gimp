@echo off
echo Installing NumPy for GIMP 3 Python environment...
echo.

REM GIMP 3 Python location
set GIMP_PYTHON="C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe"

if not exist %GIMP_PYTHON% (
    echo ERROR: Could not find GIMP Python at %GIMP_PYTHON%
    echo.
    echo Please check your GIMP installation path
    pause
    exit /b 1
)

echo Found GIMP Python at: %GIMP_PYTHON%
echo.
echo Installing numpy...
echo.

%GIMP_PYTHON% -m pip install numpy

echo.
echo Installation complete!
echo.
echo Now restart GIMP and the AI Separation plugins should appear.
echo.
pause
