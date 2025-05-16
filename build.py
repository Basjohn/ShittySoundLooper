import os
import sys
import shutil
import subprocess
from PyInstaller.__main__ import run

def check_python_version():
    """Ensure we're using Python 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)

def install_dependencies():
    """Install required Python packages."""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build_ssl():
    """Build SSL executable."""
    # Clean up previous builds
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    # Build with basic flags
    run([
        '--name=SSL',
        '--onefile',
        '--windowed',
        '--icon=resources/SSLMoon.ico',
        '--add-data=resources;resources',
        '--add-data=config.json;.',
        '--hidden-import=pycaw',
        '--hidden-import=pycaw.pycaw',
        '--hidden-import=pycaw.utils',
        '--hidden-import=pycaw.backend',
        '--hidden-import=pycaw.backend.winrt',
        '--hidden-import=pycaw.backend.winrt.coreaudio',
        '--hidden-import=pycaw.backend.winrt.coreaudio.coreaudio',
        'main.py'
    ])

def main():
    print("Starting SSL Builder...")
    check_python_version()
    install_dependencies()
    build_ssl()

if __name__ == "__main__":
    main()
