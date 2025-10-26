# WSL2 Setup Guide for GIMP 3 + AI Separation Plugins

## Why WSL2 is the Solution

**The NumPy installation problem on Windows GIMP is solved instantly with WSL2** because:

✅ **Standard Python** - Linux GIMP uses regular CPython, not custom MINGW builds
✅ **No platform tags** - NumPy installs normally from PyPI with `pip install numpy`
✅ **Native GUI support** - WSLg (built into Windows 11 & updated Windows 10) displays Linux apps seamlessly
✅ **No compilation** - Pre-built NumPy binaries work immediately
✅ **Access Windows files** - Your project directory is available at `/mnt/c/Users/atwel/...`

## Prerequisites

- **Windows 10** (version 2004+) or **Windows 11**
- **Administrator access** for initial installation
- **~5GB disk space** for Ubuntu + GIMP + dependencies

## Step-by-Step Installation

### Step 1: Install WSL2

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

This single command:
- Enables WSL and Virtual Machine Platform features
- Downloads and installs the Linux kernel
- Installs Ubuntu (default distribution)
- Sets WSL 2 as the default version

**Restart your computer** when prompted.

### Step 2: First-Time Ubuntu Setup

After restart, Ubuntu will automatically launch and ask you to:

1. **Create a username** (lowercase, no spaces - e.g., `atwel`)
2. **Create a password** (you'll need this for `sudo` commands)

Wait for the installation to complete.

### Step 3: Update Ubuntu

In the Ubuntu terminal, run:

```bash
sudo apt update && sudo apt upgrade -y
```

This ensures you have the latest packages.

### Step 4: Install GIMP 3

Ubuntu's default repos have GIMP 2.x, so we'll use a PPA or Flatpak for GIMP 3:

#### Option A: Install via Flatpak (Recommended)

```bash
# Install Flatpak
sudo apt install -y flatpak

# Add Flathub repository
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install GIMP 3
flatpak install -y flathub org.gimp.GIMP
```

#### Option B: Install via PPA (if available)

```bash
# Add GIMP PPA
sudo add-apt-repository ppa:otto-kesselgulasch/gimp-edge
sudo apt update

# Install GIMP
sudo apt install -y gimp
```

### Step 5: Install Python Dependencies

```bash
# Install Python and pip
sudo apt install -y python3 python3-pip

# Install NumPy
pip3 install numpy

# Verify NumPy installation
python3 -c "import numpy; print('NumPy', numpy.__version__, 'installed!')"
```

You should see: `NumPy 2.x.x installed!`

### Step 6: Copy Plugins to WSL

Your Windows files are accessible under `/mnt/c/`. Copy the plugin files:

```bash
# Create GIMP plugins directory
mkdir -p ~/.config/GIMP/3.0/plug-ins

# Navigate to your Windows project
cd /mnt/c/Users/atwel/OneDrive/Documents/-SepAI-gimp-main

# Copy plugin directories
cp -r ai-separation-analyze ~/.config/GIMP/3.0/plug-ins/
cp -r ai-separation-color-match ~/.config/GIMP/3.0/plug-ins/
cp -r ai-separation-separate ~/.config/GIMP/3.0/plug-ins/

# Make plugins executable
chmod +x ~/.config/GIMP/3.0/plug-ins/*/ai-separation-*.py
```

**Alternative** - Use the install script if available:

```bash
cd /mnt/c/Users/atwel/OneDrive/Documents/-SepAI-gimp-main
python3 install_plugin.py
```

### Step 7: Launch GIMP

#### If installed via Flatpak:
```bash
flatpak run org.gimp.GIMP
```

#### If installed via PPA:
```bash
gimp &
```

The `&` runs GIMP in the background so you can continue using the terminal.

**GIMP will open as a native window on your Windows desktop!** This is WSLg magic - it looks and behaves like a Windows app.

### Step 8: Verify Plugins

1. Open an image in GIMP
2. Go to **Filters → Render**
3. You should see:
   - **AI Separation: Analyze Image (Step 1)**
   - **AI Separation: Color Match (Step 2)**
   - **AI Separation: Separate Colors (Step 3)**

### Step 9: Test the Plugins

1. **Open a color image**
2. **Run Analyze** (Filters → Render → AI Separation: Analyze Image)
   - Should detect colors and display results
3. **Run Color Match** (Filters → Render → AI Separation: Color Match)
   - Should show color palette adjustment dialog
4. **Run Separate** (Filters → Render → AI Separation: Separate Colors)
   - Should create separate layers for each color

## Troubleshooting

### GIMP doesn't start with GUI

**Windows 10 users** - Update WSL:
```bash
wsl --update
```

Install GUI support manually if needed:
```powershell
# In PowerShell (as Administrator)
wsl --install --no-distribution
```

### Plugins don't appear in menu

Check plugin permissions:
```bash
ls -la ~/.config/GIMP/3.0/plug-ins/*/
```

Each `.py` file should have executable permission (`-rwxr-xr-x`). Fix with:
```bash
chmod +x ~/.config/GIMP/3.0/plug-ins/*/*.py
```

### NumPy import errors

Verify NumPy is in GIMP's Python path:
```bash
python3 -c "import sys; print('\n'.join(sys.path))"
python3 -c "import numpy; print(numpy.__file__)"
```

Reinstall if needed:
```bash
pip3 uninstall numpy
pip3 install numpy
```

### Can't find files at /mnt/c/

Ensure the C: drive is mounted:
```bash
ls /mnt/c/Users/
```

If not mounted, restart WSL:
```powershell
# In PowerShell
wsl --shutdown
# Then reopen Ubuntu
```

## Performance Notes

- **GUI performance** is excellent on modern systems
- **File access** from `/mnt/c/` is slightly slower than native Linux files
- **Consider moving project** to Linux filesystem for better performance:

```bash
# Copy project to Linux home directory
cp -r /mnt/c/Users/atwel/OneDrive/Documents/-SepAI-gimp-main ~/sepai-gimp
cd ~/sepai-gimp
```

## Advantages of WSL2 Setup

✅ **Full NumPy functionality** - All image processing works
✅ **Easy package management** - `pip install` works normally
✅ **Fast iteration** - Edit code in Windows, test in WSL
✅ **Cross-platform** - Same code works on Linux servers
✅ **No ABI issues** - Standard Python environment
✅ **Future-proof** - Easy to install any Python package

## Editing Files

You can edit plugin code from Windows using your favorite editor:

- **VSCode**: Open WSL folder directly: `File → Open Folder → \\wsl$\Ubuntu\home\<username>\`
- **Notepad++, Sublime**: Edit files at `C:\Users\atwel\OneDrive\...` as before
- **Vim/Nano**: Edit directly in Ubuntu terminal

Changes are immediately reflected when you restart GIMP.

## Creating a Desktop Shortcut (Optional)

Make GIMP easily accessible from Windows Start Menu:

1. Create a file `~/.local/share/applications/gimp.desktop`:

```bash
cat > ~/.local/share/applications/gimp.desktop << 'EOF'
[Desktop Entry]
Name=GIMP 3 (WSL)
Exec=gimp
Icon=gimp
Type=Application
Categories=Graphics;
EOF
```

2. GIMP should now appear in Windows Start Menu

## Quick Reference Commands

```bash
# Start GIMP
flatpak run org.gimp.GIMP   # or: gimp

# Update GIMP
flatpak update              # or: sudo apt upgrade gimp

# Reinstall plugins
cd /mnt/c/Users/atwel/OneDrive/Documents/-SepAI-gimp-main
python3 install_plugin.py

# Check GIMP plugin directory
ls -la ~/.config/GIMP/3.0/plug-ins/

# View GIMP error log
cat ~/.config/GIMP/3.0/gimp-errors.log

# Update NumPy
pip3 install --upgrade numpy
```

## Summary

**Total setup time**: 30-60 minutes
**Result**: Fully functional GIMP 3 with NumPy-powered AI Separation plugins
**Maintenance**: Same as native Linux - simple package updates

This approach bypasses all the Windows MINGW/LLVM platform incompatibility issues and gives you a production-ready environment in under an hour!
