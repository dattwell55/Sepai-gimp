@echo off
echo Looking for GIMP installation...

REM Try common GIMP installation paths
set GIMP_EXE=

if exist "C:\Program Files\GIMP 3\bin\gimp-3.0.exe" (
    set GIMP_EXE=C:\Program Files\GIMP 3\bin\gimp-3.0.exe
)

if exist "C:\Program Files (x86)\GIMP 3\bin\gimp-3.0.exe" (
    set GIMP_EXE=C:\Program Files (x86)\GIMP 3\bin\gimp-3.0.exe
)

if exist "C:\Program Files\GIMP 2.99\bin\gimp-2.99.exe" (
    set GIMP_EXE=C:\Program Files\GIMP 2.99\bin\gimp-2.99.exe
)

if "%GIMP_EXE%"=="" (
    echo ERROR: Could not find GIMP executable
    echo Please edit this script and set the correct path
    echo.
    echo Example: set GIMP_EXE=C:\Path\To\GIMP\bin\gimp-3.0.exe
    pause
    exit /b 1
)

echo Found GIMP at: %GIMP_EXE%
echo.
echo Starting GIMP with console output...
echo Look for any Python errors or plugin loading messages
echo.
echo Press Ctrl+C to stop GIMP when done
echo.

"%GIMP_EXE%" --verbose --console-messages

pause
