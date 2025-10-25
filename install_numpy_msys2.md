# Installing NumPy from MSYS2 for GIMP

Now that you have MSYS2 installed, follow these steps:

## Step 1: Install NumPy in MSYS2

1. **Open MSYS2 MINGW64** (NOT MSYS2 MSYS!)
   - Find it in Start Menu → MSYS2 → **MSYS2 MINGW64**
   - The terminal prompt should show `MINGW64`

2. **Install NumPy package:**
   ```bash
   pacman -S mingw-w64-x86_64-python-numpy
   ```
   - When asked "Proceed with installation? [Y/n]" press **Y**

3. **Verify installation in MSYS2:**
   ```bash
   python -c "import numpy; print(numpy.__version__)"
   ```
   - Should print something like `2.0.2` or similar

## Step 2: Copy NumPy to GIMP's Python

Now copy the NumPy package from MSYS2 to GIMP:

### Option A: Using Windows Explorer (Easier)

1. **Open source location:**
   - Navigate to: `C:\msys64\mingw64\lib\python3.12\site-packages\`
   - Find the `numpy` folder and `numpy-*.dist-info` folder

2. **Open destination location:**
   - Navigate to: `C:\Users\atwel\AppData\Local\Programs\GIMP 3\lib\python3.12\site-packages\`

3. **Copy folders:**
   - Copy `numpy` folder from MSYS2 to GIMP
   - Copy `numpy-*.dist-info` folder from MSYS2 to GIMP

### Option B: Using PowerShell Command

Open PowerShell and run:

```powershell
# Copy numpy
Copy-Item -Path "C:\msys64\mingw64\lib\python3.12\site-packages\numpy" -Destination "C:\Users\atwel\AppData\Local\Programs\GIMP 3\lib\python3.12\site-packages\numpy" -Recurse -Force

# Copy numpy dist-info
Copy-Item -Path "C:\msys64\mingw64\lib\python3.12\site-packages\numpy*.dist-info" -Destination "C:\Users\atwel\AppData\Local\Programs\GIMP 3\lib\python3.12\site-packages\" -Recurse -Force
```

## Step 3: Verify NumPy in GIMP's Python

```powershell
& "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\python.exe" -c "import numpy; print('NumPy', numpy.__version__, 'installed!')"
```

If this prints "NumPy X.X.X installed!" - **SUCCESS!**

## Step 4: Restart GIMP and Test

1. **Close GIMP completely**
2. **Restart GIMP**
3. **Open an image**
4. **Run: Filters → Render → AI Separation: Analyze Image (Step 1)**
5. **The plugin should now work with full functionality!**

---

## Troubleshooting

### If Step 2 doesn't work:
- Make sure Python versions match (both should be 3.12)
- Check that MSYS2 is installed at `C:\msys64`
- Check that GIMP is at the expected path

### If you see "module not found" errors:
The numpy package might have dependencies. Also copy these from MSYS2:
- `numpy.libs` folder (if it exists)
- Any `*-*.dist-info` folders that numpy depends on

### If GIMP Python still can't find numpy:
You might need to also copy numpy's dependencies. In MSYS2 terminal, check:
```bash
pacman -Qi mingw-w64-x86_64-python-numpy
```
Look at "Depends On" and copy those packages too if needed.
