#!/usr/bin/env python3
"""
install_plugin.py - Install AI Color Separation Plugin for GIMP 3.0

This script installs the separation plugin into GIMP's plugin directory.

Usage:
    python install_plugin.py

Or for manual installation:
    1. Copy separation_plugin.py to GIMP plugin directory
    2. Copy core/ directory to same location
    3. Make separation_plugin.py executable (Linux/Mac)
    4. Restart GIMP
"""

import os
import sys
import shutil
import platform
from pathlib import Path


def get_gimp_plugin_dir():
    """Get GIMP 3.0 plugin directory for current platform"""
    system = platform.system()

    if system == "Windows":
        # Windows: %APPDATA%\GIMP\3.0\plug-ins
        appdata = os.getenv('APPDATA')
        if appdata:
            return os.path.join(appdata, 'GIMP', '3.0', 'plug-ins')

    elif system == "Linux":
        # Linux: ~/.config/GIMP/3.0/plug-ins
        home = Path.home()
        return home / '.config' / 'GIMP' / '3.0' / 'plug-ins'

    elif system == "Darwin":  # macOS
        # macOS: ~/Library/Application Support/GIMP/3.0/plug-ins
        home = Path.home()
        return home / 'Library' / 'Application Support' / 'GIMP' / '3.0' / 'plug-ins'

    return None


def install_plugin():
    """Install the separation plugin"""
    print("="*60)
    print("AI Color Separation Plugin - Installer")
    print("="*60)
    print()

    # Get source directory (where this script is)
    source_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Source directory: {source_dir}")

    # Get GIMP plugin directory
    plugin_dir = get_gimp_plugin_dir()

    if not plugin_dir:
        print("ERROR: Could not determine GIMP plugin directory for your platform")
        print()
        print("Manual installation:")
        print("1. Find your GIMP 3.0 plug-ins directory")
        print("2. Create folder: ai-color-separation/")
        print("3. Copy separation_plugin.py to that folder")
        print("4. Copy core/ directory to that folder")
        return False

    plugin_dir = Path(plugin_dir)
    print(f"GIMP plugin directory: {plugin_dir}")

    # Create plugin subdirectory
    install_dir = plugin_dir / 'ai-color-separation'
    print(f"Installation directory: {install_dir}")
    print()

    # Check if plugin directory exists
    if not plugin_dir.exists():
        print(f"Creating GIMP plugin directory: {plugin_dir}")
        plugin_dir.mkdir(parents=True, exist_ok=True)

    # Check if already installed
    if install_dir.exists():
        response = input(f"Plugin already installed at {install_dir}\nOverwrite? (y/n): ")
        if response.lower() != 'y':
            print("Installation cancelled")
            return False

        print(f"Removing existing installation...")
        shutil.rmtree(install_dir)

    # Create installation directory
    print(f"Creating {install_dir}...")
    install_dir.mkdir(parents=True, exist_ok=True)

    # Copy plugin files (all 3 steps)
    plugin_files = [
        'analyze_plugin.py',
        'color_match_plugin.py',
        'separation_plugin.py'
    ]

    for plugin_file_name in plugin_files:
        print(f"Copying {plugin_file_name}...")
        plugin_file = os.path.join(source_dir, plugin_file_name)
        if not os.path.exists(plugin_file):
            print(f"WARNING: {plugin_file_name} not found at {plugin_file}")
            print(f"  Skipping this plugin...")
            continue

        shutil.copy2(plugin_file, install_dir / plugin_file_name)

    # Copy core modules
    print("Copying core/ directory...")
    core_dir = os.path.join(source_dir, 'core')
    if not os.path.exists(core_dir):
        print(f"ERROR: core/ directory not found at {core_dir}")
        return False

    shutil.copytree(core_dir, install_dir / 'core', dirs_exist_ok=True)

    # Copy UI directory (if exists)
    ui_dir = os.path.join(source_dir, 'ui')
    if os.path.exists(ui_dir):
        print("Copying ui/ directory...")
        shutil.copytree(ui_dir, install_dir / 'ui', dirs_exist_ok=True)

    # Copy prompts directory (if exists)
    prompts_dir = os.path.join(source_dir, 'prompts')
    if os.path.exists(prompts_dir):
        print("Copying prompts/ directory...")
        shutil.copytree(prompts_dir, install_dir / 'prompts', dirs_exist_ok=True)

    # Make executable on Unix-like systems
    if platform.system() != "Windows":
        for plugin_file_name in plugin_files:
            plugin_path = install_dir / plugin_file_name
            if plugin_path.exists():
                os.chmod(plugin_path, 0o755)
                print(f"Made {plugin_path} executable")

    print()
    print("="*60)
    print("Installation Complete!")
    print("="*60)
    print()
    print("Installed plugins:")
    print("  - Analyze Image (Step 1)")
    print("  - Color Match (Step 2)")
    print("  - Separate Colors (Step 3)")
    print()
    print("Next steps:")
    print("1. Restart GIMP")
    print("2. Look for 'AI Separation' menu under Filters")
    print("3. Run the complete 3-step workflow:")
    print("   a. Filters > AI Separation > Analyze Image (Step 1)")
    print("   b. Filters > AI Separation > Color Match (Step 2)")
    print("   c. Filters > AI Separation > Separate Colors (Step 3)")
    print()
    print("Optional: Set up Gemini API key for AI features")
    print(f"  Create file: {plugin_dir.parent / 'ai-separation' / 'gemini_api.key'}")
    print("  Add your Gemini API key to this file")
    print()

    return True


def uninstall_plugin():
    """Uninstall the separation plugin"""
    plugin_dir = get_gimp_plugin_dir()
    if not plugin_dir:
        print("ERROR: Could not determine GIMP plugin directory")
        return False

    install_dir = Path(plugin_dir) / 'ai-color-separation'

    if not install_dir.exists():
        print("Plugin not installed")
        return False

    response = input(f"Remove plugin from {install_dir}? (y/n): ")
    if response.lower() != 'y':
        print("Uninstall cancelled")
        return False

    shutil.rmtree(install_dir)
    print(f"Plugin removed from {install_dir}")
    print("Restart GIMP to complete uninstallation")

    return True


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == 'uninstall':
        return 0 if uninstall_plugin() else 1
    else:
        return 0 if install_plugin() else 1


if __name__ == "__main__":
    sys.exit(main())
