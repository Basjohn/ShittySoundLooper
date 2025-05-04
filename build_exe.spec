# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Get the absolute path to the icon file
icon_path = os.path.abspath(os.path.join('resources', 'MoonIcon.ico'))

# Add additional data files
added_files = [
    ('resources/MoonIcon.ico', 'resources'),
    ('resources/loops', 'resources/loops'),
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'pystray._win32', 
        'win32gui', 
        'win32api', 
        'win32con', 
        'PIL._tkinter_finder'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add Tcl/Tk data files for proper icon handling
if sys.platform == 'win32':
    a.datas += collect_data_files('tkinter')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    uac_admin=False,
)
