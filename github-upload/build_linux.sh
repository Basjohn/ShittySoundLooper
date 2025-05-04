#!/bin/bash

# Shitty Sound Looper - Linux Build Script
# ----------------------------------------

echo "=== Shitty Sound Looper - Linux Build Script ==="
echo "Building executable for Linux..."

# Ensure we have the required dependencies
echo "Checking dependencies..."
pip install -r requirements.txt

# Create the spec file if it doesn't exist
if [ ! -f "build_linux.spec" ]; then
    echo "Creating Linux spec file..."
    cat > build_linux.spec << 'EOL'
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Get the base directory
base_dir = os.path.abspath(os.path.dirname(__file__))
src_dir = os.path.join(base_dir, 'src')
resources_dir = os.path.join(base_dir, 'resources')

# Define paths
icon_path = os.path.abspath(os.path.join(resources_dir, 'MoonIcon.ico'))

# Define data files
added_files = [
    (os.path.join(resources_dir, 'MoonIcon.ico'), 'resources')
]

a = Analysis(
    [os.path.join(src_dir, 'main.py')],
    pathex=[base_dir],
    binaries=[],
    datas=added_files,
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add tkinter data files
a.datas += collect_data_files('tkinter')

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ShittySoundLooper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
EOL
fi

# Build the executable
echo "Building executable..."
pyinstaller build_linux.spec --clean --noconfirm

# Check if build was successful
if [ -f "dist/ShittySoundLooper" ]; then
    echo "Build successful! Executable is at: dist/ShittySoundLooper"
    echo "Creating loops directory if it doesn't exist..."
    mkdir -p dist/loops
    
    # Make the executable executable
    chmod +x dist/ShittySoundLooper
    
    echo "Done! You can now run the application with: ./dist/ShittySoundLooper"
else
    echo "Build failed. Check the output for errors."
fi
