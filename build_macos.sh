#!/bin/bash

# Shitty Sound Looper - macOS Build Script
# ----------------------------------------

echo "=== Shitty Sound Looper - macOS Build Script ==="
echo "Building application bundle for macOS..."

# Ensure we have the required dependencies
echo "Checking dependencies..."
pip3 install -r requirements.txt

# Create the spec file if it doesn't exist
if [ ! -f "build_macos.spec" ]; then
    echo "Creating macOS spec file..."
    cat > build_macos.spec << 'EOL'
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
    [],
    exclude_binaries=True,
    name='ShittySoundLooper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ShittySoundLooper',
)

app = BUNDLE(
    coll,
    name='ShittySoundLooper.app',
    icon=icon_path,
    bundle_identifier='com.shittysoundlooper',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
    },
)
EOL
fi

# Build the application
echo "Building application bundle..."
pyinstaller build_macos.spec --clean --noconfirm

# Check if build was successful
if [ -d "dist/ShittySoundLooper.app" ]; then
    echo "Build successful! Application bundle is at: dist/ShittySoundLooper.app"
    echo "Creating loops directory if it doesn't exist..."
    mkdir -p dist/ShittySoundLooper.app/Contents/Resources/loops
    
    echo "Done! You can now run the application by double-clicking dist/ShittySoundLooper.app"
else
    echo "Build failed. Check the output for errors."
fi
