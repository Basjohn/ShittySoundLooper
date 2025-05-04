from setuptools import setup, find_packages

setup(
    name="ShittySoundLooper",
    version="1.0.0",
    description="A simple utility for creating seamless audio loops",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pygame>=2.6.1",
        "customtkinter>=5.2.1",
        "pystray>=0.19.4",
        "numpy>=1.24.0",
        "pillow>=9.0.0",
    ],
    extras_require={
        "windows": ["pywin32>=306"],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Utilities",
    ],
    entry_points={
        "console_scripts": [
            "shittysoundlooper=src.main:main",
        ],
    },
)
