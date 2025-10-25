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

    # GIMP 3.0 requires each plugin in its own directory
    # with the plugin file matching the directory name

    plugins_info = [
        {
            'source': 'analyze_plugin.py',
            'dir_name': 'ai-separation-analyze',
            'plugin_name': 'ai-separation-analyze.py',
            'label': 'Analyze Image (Step 1)'
        },
        {
            'source': 'color_match_plugin.py',
            'dir_name': 'ai-separation-color-match',
            'plugin_name': 'ai-separation-color-match.py',
            'label': 'Color Match (Step 2)'
        },
        {
            'source': 'separation_plugin.py',
            'dir_name': 'ai-separation-separate',
            'plugin_name': 'ai-separation-separate.py',
            'label': 'Separate Colors (Step 3)'
        }
    ]

    # Shared directories (core, ui, prompts)
    core_dir = os.path.join(source_dir, 'core')
    ui_dir = os.path.join(source_dir, 'ui')
    prompts_dir = os.path.join(source_dir, 'prompts')

    # Install each plugin in its own directory
    for plugin_info in plugins_info:
        plugin_source = os.path.join(source_dir, plugin_info['source'])

        if not os.path.exists(plugin_source):
            print(f"WARNING: {plugin_info['source']} not found, skipping...")
            continue

        # Create plugin directory
        plugin_install_dir = plugin_dir / plugin_info['dir_name']
        print(f"\nInstalling {plugin_info['label']}...")
        print(f"  Directory: {plugin_install_dir}")

        if plugin_install_dir.exists():
            shutil.rmtree(plugin_install_dir)

        plugin_install_dir.mkdir(parents=True, exist_ok=True)

        # Copy plugin file with correct name
        print(f"  Copying {plugin_info['source']} -> {plugin_info['plugin_name']}")
        shutil.copy2(plugin_source, plugin_install_dir / plugin_info['plugin_name'])

        # Copy shared modules to each plugin directory
        if os.path.exists(core_dir):
            shutil.copytree(core_dir, plugin_install_dir / 'core', dirs_exist_ok=True)

        if os.path.exists(ui_dir):
            shutil.copytree(ui_dir, plugin_install_dir / 'ui', dirs_exist_ok=True)

        if os.path.exists(prompts_dir):
            shutil.copytree(prompts_dir, plugin_install_dir / 'prompts', dirs_exist_ok=True)

        # Make executable on Unix-like systems
        if platform.system() != "Windows":
            plugin_file_path = plugin_install_dir / plugin_info['plugin_name']
            os.chmod(plugin_file_path, 0o755)
            print(f"  Made {plugin_info['plugin_name']} executable")

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

    plugin_dir = Path(plugin_dir)

    # List of plugin directories to remove
    plugin_dirs = [
        'ai-separation-analyze',
        'ai-separation-color-match',
        'ai-separation-separate',
        'ai-color-separation'  # Old structure, in case it exists
    ]

    found_any = False
    for dir_name in plugin_dirs:
        install_dir = plugin_dir / dir_name
        if install_dir.exists():
            found_any = True
            print(f"Found: {install_dir}")

    if not found_any:
        print("Plugin not installed")
        return False

    response = input(f"Remove all AI Separation plugins? (y/n): ")
    if response.lower() != 'y':
        print("Uninstall cancelled")
        return False

    for dir_name in plugin_dirs:
        install_dir = plugin_dir / dir_name
        if install_dir.exists():
            shutil.rmtree(install_dir)
            print(f"Removed: {install_dir}")

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
