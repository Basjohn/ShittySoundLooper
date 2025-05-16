import sys
import os
import json
from pathlib import Path
import tempfile
import time
import webbrowser
import numpy as np
import wave
import pygame
import ctypes
from ctypes import wintypes
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QSlider, QLabel, QFileDialog, QFrame, QSizePolicy,
                             QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize
from PyQt6.QtGui import QPainter, QPen, QImage, QPixmap, QColor, QIcon, QAction

# Function to make a window draggable by clicking anywhere on its background
def make_window_draggable(window):
    def mousePressEvent(event):
        if event.button() == Qt.MouseButton.LeftButton:
            window.drag_position = event.globalPosition().toPoint() - window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(event):
        if event.buttons() == Qt.MouseButton.LeftButton and window.drag_position is not None:
            new_pos = event.globalPosition().toPoint() - window.drag_position
            
            # Get screen geometry
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            
            # Calculate snapping points
            snap_distance = 15  # Distance to trigger snap
            snap_points = [
                (0, 0),  # Top-left
                (screen_geometry.width(), 0),  # Top-right
                (0, screen_geometry.height()),  # Bottom-left
                (screen_geometry.width(), screen_geometry.height())  # Bottom-right
            ]
            
            # Check if we should snap
            min_distance = float('inf')
            snap_point = None
            
            for x, y in snap_points:
                distance = ((new_pos.x() - x) ** 2 + (new_pos.y() - y) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    snap_point = (x, y)
            
            # Snap if close enough to edge
            if min_distance < snap_distance:
                new_pos = QPoint(*snap_point)
                
                # Save position when snapping
                if hasattr(window, 'save_config'):
                    config = {
                        "window_position": {
                            "x": new_pos.x(),
                            "y": new_pos.y()
                        }
                    }
                    window.save_config(config)
            
            # Prevent going out of bounds
            if new_pos.x() < 0:
                new_pos.setX(0)
            if new_pos.y() < 0:
                new_pos.setY(0)
            if new_pos.x() + window.width() > screen_geometry.width():
                new_pos.setX(screen_geometry.width() - window.width())
            if new_pos.y() + window.height() > screen_geometry.height():
                new_pos.setY(screen_geometry.height() - window.height())
            
            window.move(new_pos)
            event.accept()

    def mouseReleaseEvent(event):
        window.drag_position = None
        
        # Save window position only when releasing
        if hasattr(window, 'save_config'):
            config = {
                "window_position": {
                    "x": window.x(),
                    "y": window.y()
                }
            }
            window.save_config(config)
        
        event.accept()

    window.drag_position = None
    window.mousePressEvent = mousePressEvent
    window.mouseMoveEvent = mouseMoveEvent
    window.mouseReleaseEvent = mouseReleaseEvent
from PIL import Image, ImageDraw


# Constants
DARK_THEME = {
    "bg_color": "#2E2E2E",
    "fg_color": "#F5F5F5",
    "button_color": "#222222",
    "hover_color": "#333333",
    "entry_color": "#1E1E1E",
    "border_color": "#F5F5F5",  # Updated to nearly white
    "slider_color": "#222222",
    "slider_progress": "#BBBBBB",
    "disabled_text": "#6D6D6D",
    "disabled_button": "#1D1D1D",
    "title_bar_bg": "#222222",
    "close_button_bg": "#444444",
    "window_border": "#FFFFFF",
    "divider_line": "#FFFFFF",
    "moon_box_bg": "#1C1C1C",
    "waveform_a": "#DDDDDD",
    "waveform_b": "#AAAAAA"
}

CHANNEL_A = 0
CHANNEL_B = 1

# Updated Stylesheet
STYLESHEET = """
QMainWindow {
    background-color: #FFFFFF;
}
QWidget#MainContent {
    background-color: #2E2E2E;
    border: 2px solid white;
}
QFrame#TitleBar {
    background-color: #222222;
    border: none;
    border-bottom: 3px solid white;
}
QLabel#TitleLabel {
    color: white;
    font: bold 20px 'Segoe UI';
    background-color: transparent;
}
QPushButton#CloseButton {
    background-color: #222222;
    color: white;
    border: 2px solid #F5F5F5;
    border-radius: 5px;
    font: bold 16px 'Segoe UI';
    padding: 3px;  /* Reduced padding */
}
QPushButton#CloseButton:hover {
    background-color: #333333;
}
QPushButton#CloseButton:pressed {
    background-color: #222222;
}
QFrame#StreamFrame {
    background-color: transparent;
    border: none;
}
QPushButton#BrowseButton {
    background-color: #222222;
    color: #F5F5F5;
    border: 3px solid #F5F5F5;
    border-radius: 5px;
    padding: 5px;
    min-height: 32px;
    font: 14px 'Segoe UI';
}
QPushButton#BrowseButton:hover {
    background-color: #333333;
}
QLabel#FileLabel {
    background-color: #1E1E1E;
    color: #F5F5F5;
    border: 3px solid #F5F5F5;
    border-radius: 5px;
    padding: 5px;
    min-height: 32px;
    font: 14px 'Segoe UI';
}
QPushButton#PlayButton {
    background-color: #222222;
    color: #FFFFFF;
    border: 3px solid #FFFFFF;
    border-radius: 5px;
    padding: 5px;
    min-width: 40px;
    min-height: 32px;
    font: bold 16px 'Segoe UI';
}
QPushButton#PlayButton:hover {
    background-color: #333333;
    color: #FFFFFF;
}
QPushButton#PlayButton:disabled {
    background-color: #1D1D1D;
    color: #6D6D6D;
    border: 3px solid #6D6D6D;
}
QPushButton#PlayButton:disabled {
    background-color: #1D1D1D;
    color: #6D6D6D;
}
QFrame#VolumeFrame {
    background-color: #1E1E1E;
    border: 3px solid #F5F5F5;
    border-radius: 5px;
    padding: 5px;
}
QLabel#VolumeLabel {
    color: #F5F5F5;
    background-color: transparent;
    font: 14px 'Segoe UI';
}
QSlider#VolumeSlider {
    min-height: 20px;
    background: #222222;
    border: none;
}
QSlider::groove:horizontal {
    background: #222222;
    height: 5px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #000000;  /* Black background */
    border: 3px solid #FFFFFF;  /* White border */
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #333333;
}
QSlider::sub-page:horizontal {
    background: #BBBBBB;
    border-radius: 2px;
}
QLabel#VolumeValue {
    color: #F5F5F5;
    background-color: transparent;
    font: 14px 'Segoe UI';
}
QFrame#WaveformFrame {
    background-color: #1E1E1E;
    border: 3px solid #F5F5F5;
    border-radius: 5px;
    margin: 5px;
    padding: 5px;
}
QLabel#WaveformTitle {
    color: #F5F5F5;
    background-color: transparent;
    font: bold 14px 'Segoe UI';
    margin-bottom: 0px;
    padding: 2px;
}
QFrame#ControlFrame {
    background-color: transparent;
    border: none;
}
QPushButton#PlayAllButton {
    background-color: #222222;
    color: #FFFFFF;
    border: 3px solid #FFFFFF;
    border-radius: 5px;
    min-width: 60px;
    min-height: 60px;
    font: bold 22px 'Segoe UI';
}
QPushButton#PlayAllButton:hover {
    background-color: #333333;
    color: #FFFFFF;
}
QPushButton#MinimizeButton, QPushButton#SettingsButton {
    background-color: #222222;
    color: #F5F5F5;
    border: 3px solid #F5F5F5;
    border-radius: 5px;
    padding: 5px;
    min-height: 32px;
    font: 14px 'Segoe UI';
}
QPushButton#MinimizeButton:hover, QPushButton#SettingsButton:hover {
    background-color: #333333;
}
QPushButton#AboutButton {
    background-color: #222222;
    color: #F5F5F5;
    border: 3px solid #F5F5F5;
    border-radius: 5px;
    min-width: 30px;
    min-height: 30px;
    font: 14px 'Segoe UI';
}
QPushButton#AboutButton:hover {
    background-color: #333333;
}
QLabel#MoonLabel {
    background-color: transparent;
    color: #AAAAAA;
    font: bold 18px 'Segoe UI';
}
QDialog {
    background-color: #2E2E2E;
    color: #F5F5F5;
}
QLabel#DialogLabel {
    color: #F5F5F5;
    font: 14px 'Segoe UI';
}
QPushButton#DialogButton {
    background-color: #222222;
    color: #F5F5F5;
    border: 3px solid #F5F5F5;
    border-radius: 5px;
    padding: 5px;
    min-width: 100px;
    min-height: 32px;
    font: 14px 'Segoe UI';
}
QPushButton#DialogButton:hover {
    background-color: #333333;
}
"""

class AudioStream:
    def __init__(self, parent, layout, channel_id):
        self.parent = parent
        self.channel_id = channel_id
        self.audio_file = ""
        self.sound = None
        self.temp_file = None
        self.playing = False
        self.start_ts = 0.0

        # UI
        stream_frame = QFrame()
        stream_frame.setObjectName("StreamFrame")
        stream_layout = QHBoxLayout(stream_frame)
        stream_layout.setContentsMargins(0, 5, 0, 0)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setObjectName("BrowseButton")
        self.browse_btn.setFixedWidth(90)
        self.browse_btn.clicked.connect(self.browse_file)
        stream_layout.addWidget(self.browse_btn)

        # Create a custom label that clears file contents on double-click
        class FileLabel(QLabel):
            def __init__(self, parent):
                super().__init__("Select an audio file…")
                self.parent = parent
                
                # Set tooltip style
                self.setStyleSheet("""
                    QToolTip {
                        background-color: #333333;
                        color: white;
                        border: 1px solid #888888;
                        padding: 2px;
                        border-radius: 3px;
                    }
                """)
                self.setToolTip("Double-Click To Clear")

            def mouseDoubleClickEvent(self, event):
                # Clear the file and reset everything
                self.setText("Select an audio file…")
                self.parent.audio_file = ""
                self.parent.sound = None
                self.parent.temp_file = None
                self.parent.play_btn.setDisabled(True)
                self.parent.play_btn.setText("▶")
                self.parent.playing = False
                self.parent.parent.redraw_waveform()
                self.parent.parent.update_play_all_button()
                event.accept()

        self.file_label = FileLabel(self)
        self.file_label.setObjectName("FileLabel")
        self.file_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        stream_layout.addWidget(self.file_label)

        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("PlayButton")
        self.play_btn.setFixedWidth(40)
        self.play_btn.setDisabled(True)
        self.play_btn.clicked.connect(self.play_pause)
        stream_layout.addWidget(self.play_btn)

        layout.addWidget(stream_frame)

        # Volume slider row
        vol_frame = QFrame()
        vol_frame.setObjectName("VolumeFrame")
        vol_layout = QHBoxLayout(vol_frame)
        vol_layout.setContentsMargins(0, 5, 0, 10)

        vol_label = QLabel("Volume:")
        vol_label.setObjectName("VolumeLabel")
        vol_layout.addWidget(vol_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("VolumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(10)
        self.volume_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.volume_slider.valueChanged.connect(self.on_volume)
        vol_layout.addWidget(self.volume_slider)

        self.volume_val = QLabel("10%")
        self.volume_val.setObjectName("VolumeValue")
        vol_layout.addWidget(self.volume_val)

        layout.addWidget(vol_frame)

    def browse_file(self):
        initial_dir = self.parent.last_dir if self.parent.last_dir else os.path.expanduser("~")
        filename, _ = QFileDialog.getOpenFileName(
            self.parent, "Select Audio File", initial_dir,
            "Audio Files (*.wav *.mp3 *.ogg);;WAV Files (*.wav);;MP3 Files (*.mp3);;OGG Files (*.ogg);;All Files (*.*)"
        )
        if not filename:
            return
        self.parent.last_dir = os.path.dirname(filename)
        self.load_file(filename)

    def load_file(self, filename):
        self.cleanup_temp()
        self.audio_file = filename
        self.file_label.setText(os.path.basename(filename))

        self.sound, self.temp_file, dur = self.parent.make_loopable_sound(filename)
        if self.sound:
            self.play_btn.setEnabled(True)
            self.set_volume(self.volume_slider.value())
            self.parent.redraw_waveform()

    def play_pause(self):
        ch = pygame.mixer.Channel(self.channel_id)
        if not self.playing:
            if self.sound is None:
                return
            ch.play(self.sound, loops=-1)
            self.start_ts = time.monotonic()
            self.playing = True
            self.play_btn.setText("||")  # Pause symbol
            self.parent.redraw_waveform()
            self.parent.update_play_all_button()
        else:
            ch.stop()
            self.playing = False
            self.play_btn.setText("▶")
            self.parent.redraw_waveform()
            self.parent.update_play_all_button()

    def stop(self):
        pygame.mixer.Channel(self.channel_id).stop()
        self.playing = False
        self.play_btn.setText("▶")

    def start(self):
        if self.sound:
            ch = pygame.mixer.Channel(self.channel_id)
            ch.stop()
            ch.play(self.sound, loops=-1)
            self.playing = True
            self.start_ts = time.monotonic()
            self.play_btn.setText("||")  # Pause symbol

    def set_volume(self, val):
        if self.sound:
            self.sound.set_volume(val / 100.0)

    def on_volume(self, v):
        self.volume_val.setText(f"{v}%")
        self.set_volume(v)

    def pos_fraction(self):
        if not self.playing or not self.sound:
            return None
        length = self.sound.get_length()
        if length == 0:
            return None
        delta = (time.monotonic() - self.start_ts) % length
        return delta / length

    def cleanup_temp(self):
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except Exception as e:
                print(f"Warning: Failed to remove temp file: {e}")
        self.temp_file = None  # Clear the reference to prevent potential circular references

    def to_cfg(self):
        return {
            "file": self.audio_file,
            "volume": self.volume_slider.value()
        }

    def from_cfg(self, dct):
        file_ = dct.get("file", "")
        vol = dct.get("volume", 10)
        self.volume_slider.setValue(vol)
        self.volume_val.setText(f"{int(vol)}%")
        if file_ and os.path.exists(file_):
            self.load_file(file_)

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedWidth(60)  # Slightly narrower to fit in frame
        self.setMinimumHeight(200)  # Height for the vertical waveform
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.image = None
        self.marker_pos = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.image:
            # Save the current transformation
            painter.save()
            # Translate and rotate for vertical orientation
            painter.translate(self.width(), 0)
            painter.rotate(90)
            painter.drawPixmap(0, 0, self.image)
            painter.restore()

        # Draw the marker line vertically
        pen = QPen(QColor("#FFFFFF"), 2)
        painter.setPen(pen)
        painter.drawLine(0, self.marker_pos, self.width(), self.marker_pos)

    def update_waveform(self, image):
        self.image = image
        self.update()

    def update_marker(self, pos):
        self.marker_pos = pos
        self.update()

class ShittySoundLooper(QMainWindow):
    def __init__(self):
        super().__init__()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
        # Handle PyInstaller bundle path
        if getattr(sys, 'frozen', False):
            # Running as a bundled executable
            self.base_path = Path(sys._MEIPASS)
            # Store config next to the executable for portability
            self.config_file = Path(sys.executable).parent / 'config.json'
        else:
            # Running as a script
            self.base_path = Path(os.path.dirname(os.path.abspath(__file__)))
            self.config_file = self.base_path / "config.json"
        self.last_dir = os.path.expanduser("~")
        self.minimized = False
        self.exit_requested = False
        self.drag_position = None
        self.prevent_sleep = False
        self.sleep_prevention_handle = None
        
        # Initialize window
        self.setWindowTitle("SSL")  # Taskbar title
        self.setWindowIconText("Shitty Sound Looper")  # Task Manager title
        self.setGeometry(100, 100, 620, 480)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowIcon(QIcon(str(self.base_path / 'resources' / 'SSLMoon.ico')))
        
        # Make main window draggable
        make_window_draggable(self)
        
        # Create system tray icon
        self.create_system_tray_icon()
        
        # Setup UI
        self.setup_ui()
        self.stream_a = AudioStream(self, self.main_layout, CHANNEL_A)
        self.stream_b = AudioStream(self, self.main_layout, CHANNEL_B)
        self.create_moon_image()
        
        # Load and apply transparency from config
        config = self.load_config()
        self.is_transparent = config.get('transparent_window', True)  # Default to True
        self.prevent_sleep = config.get('prevent_sleep', False)
        self.restore_volume = config.get('restore_volume', False)
        self.restore_volume_level = config.get('restore_volume_level', 50)
        self.toggle_transparency(Qt.CheckState.Checked if self.is_transparent else Qt.CheckState.Unchecked)
        
        # Initialize streams with saved settings
        stream_a_cfg = config.get('stream_a', {})
        stream_b_cfg = config.get('stream_b', {})
        self.stream_a.from_cfg(stream_a_cfg)
        self.stream_b.from_cfg(stream_b_cfg)

        # Connect play buttons to volume restoration
        self.stream_a.play_btn.clicked.connect(self.restore_system_volume)
        self.stream_b.play_btn.clicked.connect(self.restore_system_volume)
        self.play_all_btn.clicked.connect(self.restore_system_volume)
        
        # Start timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_marker)
        self.timer.start(50)

    def restore_system_volume(self):
        if not self.restore_volume:
            return
            
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            
            # Get default audio device
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            volume = interface.QueryInterface(IAudioEndpointVolume)
            
            # Convert our 0-100 scale to the Windows volume scale (0.0-1.0)
            win_volume = self.restore_volume_level / 100.0
            
            # Set the volume
            volume.SetMasterVolumeLevelScalar(win_volume, None)
            
        except Exception as e:
            print(f"Error restoring volume: {e}")

    def setup_ui(self):
        main_widget = QWidget()
        main_widget.setObjectName("MainContent")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        self.setCentralWidget(main_widget)

        # Title bar
        title_bar = QFrame()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(44)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 2, 10, 2)  # Adjusted margins

        title_label = QLabel("SHITTY SOUND LOOPER")
        title_label.setObjectName("TitleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(25, 25)  # 30% smaller to fit
        close_btn.clicked.connect(self.confirm_exit)
        title_layout.addWidget(close_btn)
        close_btn.raise_()  # Ensure it’s on top

        main_layout.addWidget(title_bar)

        # Content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Left side (streams)
        left_widget = QWidget()
        self.main_layout = QVBoxLayout(left_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Control buttons
        control_frame = QFrame()
        control_frame.setObjectName("ControlFrame")
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 10, 0, 0)

        self.play_all_btn = QPushButton("▶")
        self.play_all_btn.setObjectName("PlayAllButton")
        self.play_all_btn.clicked.connect(self.play_all)
        control_layout.addWidget(self.play_all_btn)

        about_btn = QPushButton("?")
        about_btn.setObjectName("AboutButton")
        about_btn.setFixedWidth(30)  # Just wide enough for the text
        about_btn.clicked.connect(self.show_about)
        control_layout.addWidget(about_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.main_layout.addWidget(control_frame)

        about_frame = QFrame()
        about_frame.setObjectName("ControlFrame")
        about_layout = QHBoxLayout(about_frame)
        about_layout.setContentsMargins(0, 5, 0, 5)
        about_layout.setSpacing(5)
        minimize_btn = QPushButton("Minimize")
        minimize_btn.setObjectName("MinimizeButton")
        minimize_btn.clicked.connect(self.toggle_minimize)
        about_layout.addWidget(minimize_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("SettingsButton")
        settings_btn.clicked.connect(self.open_settings)
        about_layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.main_layout.addWidget(about_frame)

        content_layout.addWidget(left_widget)

        # Right side (waveform and moon)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)  # Reduce spacing between elements

        # Create a container for waveform and its label
        waveform_container = QWidget()
        waveform_container_layout = QVBoxLayout(waveform_container)
        waveform_container_layout.setContentsMargins(0, 0, 0, 0)
        waveform_container_layout.setSpacing(2)  # Minimal spacing

        # Waveform title
        waveform_label = QLabel("WAVEFORM")
        waveform_label.setObjectName("WaveformTitle")
        waveform_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        waveform_container_layout.addWidget(waveform_label)

        # Waveform frame
        waveform_frame = QFrame()
        waveform_frame.setObjectName("WaveformFrame")
        waveform_frame.setFixedWidth(100)
        waveform_frame.setMinimumHeight(250)
        waveform_layout = QVBoxLayout(waveform_frame)
        waveform_layout.setContentsMargins(10, 10, 10, 10)

        # Waveform widget
        self.waveform_widget = WaveformWidget(self)
        waveform_layout.addWidget(self.waveform_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        waveform_container_layout.addWidget(waveform_frame)

        # Add waveform container to right layout
        right_layout.addWidget(waveform_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Moon image at bottom
        self.moon_label = QLabel()
        self.moon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.moon_label.setFixedSize(150, 150)  # Initial size, will be updated when image loads
        right_layout.addWidget(self.moon_label, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)

        content_layout.addWidget(right_widget, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(content_widget)

        self.setStyleSheet(STYLESHEET)

    def create_moon_image(self):
        moon_path = str(self.base_path / 'resources' / 'Moon_Overlay2.png')
        try:
            # Get the device pixel ratio
            ratio = self.devicePixelRatio()
            target_size = QSize(150, 150)
            target_scaled = QSize(int(target_size.width() * ratio),
                                int(target_size.height() * ratio))

            # Load the image
            pixmap = QPixmap(moon_path)
            if not pixmap.isNull():
                # Scale considering device pixel ratio
                scaled = pixmap.scaled(target_scaled,
                                     Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
                scaled.setDevicePixelRatio(ratio)

                self.moon_label.setPixmap(scaled)
                self.moon_label.setFixedSize(target_size)
        except Exception as e:
            print(f"Error loading moon image: {e}")

    def make_loopable_sound(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        temp_file = None
        duration = 0
        try:
            if ext == ".wav":
                temp_file, duration = self.create_zero_cross_loop(filename)
                snd_file = temp_file or filename
            else:
                snd_file = filename

            sound = pygame.mixer.Sound(snd_file)
            duration = sound.get_length()
            return sound, temp_file, duration
        except Exception as e:
            print(f"[ERROR] loading {filename}: {e}")
            return None, None, 0

    def create_zero_cross_loop(self, filename):
        with wave.open(filename, 'rb') as wf:
            n_channels = wf.getnchannels()
            samp_w = wf.getsampwidth()
            rate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        dtype = {1: np.int8, 2: np.int16, 4: np.int32}.get(samp_w, np.int16)
        data = np.frombuffer(raw, dtype=dtype)
        if n_channels == 2:
            analysis = data[::2]
        else:
            analysis = data
        start = int(0.1 * rate)
        end = int(0.7 * rate)
        starts = np.where(np.diff(np.signbit(analysis[start:start+rate])))[0] + start
        ends = np.where(np.diff(np.signbit(analysis[end:end+rate])))[0] + end
        start_idx = starts[0] if len(starts) else 0
        end_idx = ends[0] if len(ends) else len(analysis)-1
        if n_channels == 2:
            start_idx *= 2
            end_idx *= 2
        loop_data = data[start_idx:end_idx]
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with wave.open(temp.name, 'wb') as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(samp_w)
            wf.setframerate(rate)
            wf.writeframes(loop_data.tobytes())
        dur = (end_idx - start_idx) / rate / n_channels
        return temp.name, dur

    def play_all(self):
        # If any stream is playing, stop both
        if self.stream_a.playing or self.stream_b.playing:
            self.stream_a.stop()
            self.stream_b.stop()
            self.update_power_management()
        else:
            # Start both streams if neither is playing
            self.stream_a.start()
            self.stream_b.start()
            self.update_power_management()
        self.update_play_all_button()
        self.redraw_waveform()

    def update_play_all_button(self):
        # Update button text based on any playing stream
        if self.stream_a.playing or self.stream_b.playing:
            self.play_all_btn.setText("||")  # Pause symbol
        else:
            self.play_all_btn.setText("▶")

    def redraw_waveform(self):
        # For vertical orientation, swap width and height
        w = self.waveform_widget.height() or 200  # Height becomes width in rotated view
        h = self.waveform_widget.width() or 80    # Width becomes height in rotated view
        img = Image.new("RGB", (w, h), DARK_THEME["entry_color"])
        draw = ImageDraw.Draw(img)

        def draw_stream(stream, colour):
            if not stream.sound:
                return
            array = pygame.sndarray.array(stream.sound)
            if array.ndim == 2:
                array = array[:, 0]
            step = max(1, len(array) // w)
            points = array[::step]
            maxv = np.max(np.abs(points)) or 1
            points = (points / maxv) * (h // 2 - 2)
            mid = h // 2
            for x, val in enumerate(points[:w]):
                y0 = mid - val
                y1 = mid + val
                draw.line((x, y0, x, y1), fill=colour)

        draw_stream(self.stream_a, DARK_THEME["waveform_a"])
        draw_stream(self.stream_b, DARK_THEME["waveform_b"])

        qimage = QImage(img.tobytes(), w, h, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.waveform_widget.update_waveform(pixmap)

    def update_marker(self):
        frac = None
        for s in (self.stream_a, self.stream_b):
            f = s.pos_fraction()
            if f is not None:
                frac = f
                break
        if frac is not None:
            w = self.waveform_widget.width() or 400
            x = int(frac * w)
            self.waveform_widget.update_marker(x)
        else:
            self.waveform_widget.update_marker(0)

    def open_settings(self):
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton)
        from PyQt6.QtCore import Qt
        
        # Create settings dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        dlg.setGeometry(0, 0, 400, 250)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.FramelessWindowHint)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #2E2E2E;
                color: white;
                border: 2px solid white;
            }
            QLabel {
                color: white;
            }
            QLabel#DialogTitle {
                font: bold 16pt 'Segoe UI';
            }
            QCheckBox::indicator {
                color: #2E2E2E;
            }
            QCheckBox {
                color: white;
            }
            QSlider {
                background-color: #2E2E2E;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #444444;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #CCCCCC;
            }
            QPushButton {
                background-color: #222222;
                color: white;
                border: 3px solid white;
                border-radius: 5px;
                padding: 5px;
            }
            QSlider {
                background-color: #2E2E2E;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #444444;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #CCCCCC;
            }
            QPushButton {
                background-color: #222222;
                color: white;
                border: 3px solid white;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QPushButton#CloseButton {
                background-color: #444444;
                color: white;
                border: 2px solid white;
                border-radius: 5px;
                font: bold 14px 'Segoe UI';
                padding: 4px 2px;  /* Increased padding to make it taller */
                margin-top: 2px;
                margin-bottom: 2px;
            }
            QPushButton#CloseButton:hover {
                background-color: #555555;
            }
            QPushButton#CloseButton:pressed {
                background-color: #444444;
            }
        """)
        make_window_draggable(dlg)
        
        # Create main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add title bar with close button
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)


        
        title_label = QLabel("Settings")
        title_label.setObjectName("DialogTitle")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(25, 25)  # Match main window size
        close_btn.clicked.connect(dlg.close)
        title_layout.addWidget(close_btn)
        
        content_layout.addWidget(title_bar)
        
        # Add transparent window checkbox
        self.transparent_checkbox = QCheckBox("Enable Transparent Badassness")
        self.transparent_checkbox.setChecked(self.is_transparent)
        self.transparent_checkbox.stateChanged.connect(self.toggle_transparency)
        content_layout.addWidget(self.transparent_checkbox)

        # Add prevent sleep checkbox
        self.prevent_sleep_cb = QCheckBox("Prevent System Sleep")
        self.prevent_sleep_cb.setChecked(self.prevent_sleep)
        self.prevent_sleep_cb.stateChanged.connect(lambda state: self.save_settings(settings={
            'prevent_sleep': state == Qt.CheckState.Checked
        }))
        content_layout.addWidget(self.prevent_sleep_cb)

        # Add spacing before volume restoration
        content_layout.addSpacing(20)

        # Add restore volume option
        self.restore_volume_cb = QCheckBox("Restore System Volume Memory")
        self.restore_volume_cb.setObjectName("DialogCheckbox")
        self.restore_volume_cb.setChecked(self.restore_volume)
        self.restore_volume_cb.stateChanged.connect(lambda state: self.save_settings(settings={
            'restore_volume': state == Qt.CheckState.Checked
        }))
        content_layout.addWidget(self.restore_volume_cb)

        # Add volume slider with percentage display
        volume_frame = QFrame()
        volume_frame.setObjectName("DialogFrame")
        volume_layout = QHBoxLayout(volume_frame)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add volume slider
        volume_slider = QSlider(Qt.Orientation.Horizontal)
        volume_slider.setObjectName("DialogSlider")
        volume_slider.setRange(0, 100)
        volume_slider.setValue(self.restore_volume_level)
        volume_slider.setFixedWidth(200)  # Set fixed width to prevent stretching
        volume_slider.setFixedHeight(25)  # Set fixed height to prevent visual issues
        
        # Store the slider reference for later use
        self.volume_slider = volume_slider
        
        # Connect value change signals
        volume_slider.valueChanged.connect(lambda val: self.volume_percent.setText(f"{val}%"))
        volume_slider.valueChanged.connect(lambda val: self.save_settings(settings={
            'restore_volume_level': val
        }))
        
        # Add slider to layout before the label
        volume_layout.addWidget(volume_slider)
        
        # Add percentage label
        self.volume_percent = QLabel(f"{self.restore_volume_level}%")
        self.volume_percent.setObjectName("DialogLabel")
        self.volume_percent.setFixedWidth(40)  # Fixed width for consistent alignment
        volume_layout.addWidget(self.volume_percent)
        
        # Add spacing around the volume frame
        content_layout.addSpacing(10)
        content_layout.addWidget(volume_frame)
        content_layout.addSpacing(10)

        # Add spacing after volume restoration
        content_layout.addSpacing(20)

        # Add save button
        save_btn = QPushButton("SAVE")
        save_btn.setObjectName("DialogButton")
        save_btn.clicked.connect(lambda: self.save_settings(dialog=dlg))
        content_layout.addWidget(save_btn)
        
        # Set the main content widget as the central widget
        dlg.setLayout(QVBoxLayout())
        dlg.layout().addWidget(content_widget)
        
        dlg.exec()

    def save_settings(self, dialog=None, settings=None):
        """Save settings either from dialog or from individual updates"""
        if settings is None:
            # Update from dialog
            self.is_transparent = self.transparent_checkbox.isChecked()
            self.prevent_sleep = self.prevent_sleep_cb.isChecked()
            self.restore_volume = self.restore_volume_cb.isChecked()
            self.save_config()
            self.update_power_management()
            if dialog:
                dialog.accept()
        else:
            # Update individual settings
            for key, value in settings.items():
                setattr(self, key, value)
            self.save_config(settings)
        self.update_power_management()

    def toggle_transparency(self, state):
        # Update transparency immediately
        self.is_transparent = state == Qt.CheckState.Checked
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, self.is_transparent)
        
        # Update style sheet
        bg_color = "rgba(46, 46, 46, 0.8)" if self.is_transparent else "#2E2E2E"
        self.setStyleSheet(STYLESHEET + f"\nQWidget#MainContent {{ background-color: {bg_color}; }}")
        
        # Force repaint
        self.update()
        
        # Save to config
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except:
            config = {}
        
        config['transparent_window'] = self.is_transparent
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Ensure all required settings exist with defaults
                if 'transparent_window' not in config:
                    config['transparent_window'] = True
                if 'prevent_sleep' not in config:
                    config['prevent_sleep'] = False
                if 'restore_volume' not in config:
                    config['restore_volume'] = False
                if 'restore_volume_level' not in config:
                    config['restore_volume_level'] = 50
                return config
        except Exception:
            return {
                'transparent_window': True,
                'prevent_sleep': False,
                'restore_volume': False,
                'restore_volume_level': 50
            }

    def save_config(self, config=None):
        try:
            # Load existing config
            with open(self.config_file, 'r') as f:
                existing_config = json.load(f)
        except Exception:
            existing_config = {}

        # Update with new values
        if config is not None:
            existing_config.update(config)
        else:
            existing_config.update({
                'transparent_window': self.is_transparent,
                'prevent_sleep': self.prevent_sleep,
                'restore_volume': self.restore_volume,
                'restore_volume_level': self.restore_volume_level,
                'stream_a': self.stream_a.to_cfg(),
                'stream_b': self.stream_b.to_cfg()
            })

        try:
            with open(self.config_file, 'w') as f:
                json.dump(existing_config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def show_about(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("About Shitty Sound Looper")
        dlg.setGeometry(0, 0, 420, 260)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.FramelessWindowHint)
        dlg.setStyleSheet('''
            QDialog {
                background-color: #2E2E2E;
                color: white;
                border: 2px solid white;
            }
            QLabel {
                color: white;
            }
            QLabel#DialogTitle {
                font: bold 16pt 'Segoe UI';
            }
            QCheckBox::indicator {
                color: #2E2E2E;
            }
            QCheckBox {
                color: white;
            }
            QSlider {
                background-color: #2E2E2E;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #444444;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #CCCCCC;
            }
            QPushButton {
                background-color: #222222;
                color: white;
                border: 3px solid white;
                border-radius: 5px;
                padding: 5px;
            }
            QSlider {
                background-color: #2E2E2E;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #444444;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #CCCCCC;
            }
            QPushButton {
                background-color: #222222;
                color: white;
                border: 3px solid white;
                border-radius: 5px;
                padding: 5px;
                font: bold 22px 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QPushButton#CloseButton {
                background-color: #444444;
                color: white;
                border: 2px solid white;
                border-radius: 5px;
                font: bold 14px 'Segoe UI';
                padding: 2px;
                margin-top: 2px;
                margin-bottom: 2px;
            }
            QPushButton#CloseButton:hover {
                background-color: #555555;
            }
            QPushButton#CloseButton:pressed {
                background-color: #444444;
            }
        ''')
        make_window_draggable(dlg)
        
        # Create main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add title bar with close button
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)  # Add left and right margins
        title_layout.setSpacing(5)
        
        # Add stretch before close button
        title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(25, 25)  # Match main window size
        close_btn.clicked.connect(dlg.close)
        title_layout.addWidget(close_btn)
        
        content_layout.addWidget(title_bar)

        # Main content
        content_layout.addSpacing(20)
        
        # Centered message
        msg = ("Made for my own shitty sleep, shared freely for yours.\n"
               "You can always donate to my dumbass though or buy my shitty literature.")
        label = QLabel(msg)
        label.setObjectName("DialogLabel")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(label)

        # Button container
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)
        
        for txt, url in (("PayPal", "https://www.paypal.com/donate/?business=UBZJY8KHKKLGC&no_recurring=0&item_name=Why+are+you+doing+this%3F+Are+you+drunk%3F¤cy_code=USD"),
                         ("Goodreads", "https://www.goodreads.com/book/show/25006763-usu"),
                         ("Amazon", "https://www.amazon.com/Usu-Jayde-Ver-Elst-ebook/dp/B00V8A5K7Y")):
            btn = QPushButton(txt)
            btn.setObjectName("DialogButton")
            btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            btn_layout.addWidget(btn)
        
        content_layout.addWidget(btn_frame)
        content_layout.addSpacing(10)
        
        # Set the main content widget as the central widget
        dlg.setLayout(QVBoxLayout())
        dlg.layout().addWidget(content_widget)

        dlg.exec()

    def create_system_tray_icon(self):
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Get the correct path for the icon
        icon_path = str(self.base_path / 'resources' / 'SSLMoon.ico')
        if not os.path.exists(icon_path):
            print(f"Warning: Icon file not found at {icon_path}")
            icon_path = str(self.base_path / 'SSLMoon.ico')  # Fall back to root as last resort
        
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setToolTip("Shitty Sound Looper")
        
        # Create tray menu
        tray_menu = QMenu()
        restore_action = tray_menu.addAction("Restore")
        restore_action.triggered.connect(self.restore_from_mini)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(lambda: self.confirm_exit(True))
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        # Restore window on double-click or single-click
        if reason in [QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger]:
            self.restore_from_mini()

    def toggle_minimize(self):
        if not self.minimized:
            self.hide()
            self.minimized = True
        else:
            self.restore_from_mini()

    def restore_from_mini(self):
        self.show()
        self.activateWindow()
        self.minimized = False

    def confirm_exit(self, from_tray=False):
        if from_tray:
            # Immediate exit when called from system tray
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            self.close()
            return
        
        if self.exit_requested:
            # Remove system tray icon before closing
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            self.close()
            return
        
        self.exit_requested = True
        close_btn = self.findChild(QPushButton, "CloseButton")
        close_btn.setText("✓")
        close_btn.setStyleSheet("background-color: #222222;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            snapped_pos = self.snap_to_screen_edges(new_pos)
            self.move(snapped_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def snap_to_screen_edges(self, pos):
        # Get all screens and their geometries
        screens = QApplication.screens()
        screen_rects = [screen.geometry() for screen in screens]
        
        # Get current window size
        window_rect = self.geometry()
        window_width = window_rect.width()
        window_height = window_rect.height()
        
        # Find the screen we're currently on
        current_screen = None
        for screen in screens:
            if screen.geometry().contains(pos):
                current_screen = screen
                break
        
        if current_screen is None:
            # If we can't determine the screen, just use the first one
            current_screen = screens[0]
        
        # Calculate potential snap positions
        snap_positions = []
        
        # Check for snap points on all screens
        for screen_rect in screen_rects:
            # Left edge
            if abs(pos.x() - screen_rect.left()) <= 10:
                snap_positions.append(QPoint(screen_rect.left(), pos.y()))
            
            # Right edge
            if abs(pos.x() + window_width - screen_rect.right()) <= 10:
                snap_positions.append(QPoint(screen_rect.right() - window_width, pos.y()))
            
            # Top edge
            if abs(pos.y() - screen_rect.top()) <= 10:
                snap_positions.append(QPoint(pos.x(), screen_rect.top()))
            
            # Bottom edge
            if abs(pos.y() + window_height - screen_rect.bottom()) <= 10:
                snap_positions.append(QPoint(pos.x(), screen_rect.bottom() - window_height))
        
        # If we have snap positions, use the closest one
        if snap_positions:
            closest = min(snap_positions, key=lambda p: (p.x() - pos.x())**2 + (p.y() - pos.y())**2)
            return closest
        
        # Find the screen that would contain this position
        target_screen = None
        for screen_rect in screen_rects:
            if (screen_rect.left() <= pos.x() <= screen_rect.right() - window_width and
                screen_rect.top() <= pos.y() <= screen_rect.bottom() - window_height):
                target_screen = screen_rect
                break
        
        # If we found a valid screen, use its bounds
        if target_screen:
            x = max(target_screen.left(), min(pos.x(), target_screen.right() - window_width))
            y = max(target_screen.top(), min(pos.y(), target_screen.bottom() - window_height))
            return QPoint(x, y)
        
        # If no valid screen found, find the closest screen
        closest_screen = min(screen_rects, key=lambda r: 
            abs(pos.x() - r.left()) + abs(pos.y() - r.top()))
        
        # Position window on closest screen
        x = max(closest_screen.left(), min(pos.x(), closest_screen.right() - window_width))
        y = max(closest_screen.top(), min(pos.y(), closest_screen.bottom() - window_height))
        return QPoint(x, y)

    def closeEvent(self, event):
        try:
            # Release power management handle
            if self.sleep_prevention_handle:
                try:
                    ctypes.windll.kernel32.CloseHandle(self.sleep_prevention_handle)
                except Exception as e:
                    print(f"Warning: Failed to close sleep prevention handle: {e}")
                finally:
                    self.sleep_prevention_handle = None
            
            # Reset power management state
            try:
                ctypes.windll.kernel32.SetThreadExecutionState(wintypes.DWORD(0x80000000))  # ES_CONTINUOUS
            except Exception as e:
                print(f"Warning: Failed to reset power management state: {e}")
            
            # Save all settings
            config = {
                'transparent_window': self.is_transparent,
                'prevent_sleep': self.prevent_sleep,
                'restore_volume': self.restore_volume,
                'restore_volume_level': self.restore_volume_level,
                'last_dir': self.last_dir,
                'window_position': {'x': self.x(), 'y': self.y()},
                'stream_a': self.stream_a.to_cfg(),
                'stream_b': self.stream_b.to_cfg()
            }
            try:
                self.save_config(config)
            except Exception as e:
                print(f"Warning: Failed to save config: {e}")
            
            # Clean up audio streams and mixer
            try:
                if hasattr(self, 'stream_a'):
                    self.stream_a.stop()
                    self.stream_a.cleanup_temp()
                if hasattr(self, 'stream_b'):
                    self.stream_b.stop()
                    self.stream_b.cleanup_temp()
            except Exception as e:
                print(f"Warning: Failed to cleanup audio streams: {e}")
            
            # Clean up mixer if initialized
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.stop()
                    pygame.mixer.quit()
            except Exception as e:
                print(f"Warning: Failed to quit mixer: {e}")
            
            # Clean up system tray
            if hasattr(self, 'tray_icon'):
                try:
                    self.tray_icon.hide()
                except Exception as e:
                    print(f"Warning: Failed to hide tray icon: {e}")
            
            # Clean up timer
            if hasattr(self, 'timer'):
                try:
                    if self.timer.isActive():
                        self.timer.stop()
                    self.timer.deleteLater()  # Properly clean up the timer object
                except Exception as e:
                    print(f"Warning: Failed to clean up timer: {e}")
            
            # Clean up window
            try:
                self.hide()
            except Exception as e:
                print(f"Warning: Failed to hide window: {e}")
            
            event.accept()
            
        except Exception as e:
            print(f"Critical error during cleanup: {e}")
            event.accept()

    def update_power_management(self):
        # Release existing handle if it exists
        if self.sleep_prevention_handle:
            self.sleep_prevention_handle = None
        
        # Only prevent sleep if enabled and audio is playing
        if self.prevent_sleep and (self.stream_a.playing or self.stream_b.playing):
            # Set the execution state to prevent sleep
            ctypes.windll.kernel32.SetThreadExecutionState(
                wintypes.DWORD(0x80000000 | 0x00000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            )
        else:
            # Reset to normal power management
            ctypes.windll.kernel32.SetThreadExecutionState(
                wintypes.DWORD(0x80000000)  # ES_CONTINUOUS
            )

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Ensure we have all required settings with defaults
                    if 'transparent_window' not in config:
                        config['transparent_window'] = True
                    if 'prevent_sleep' not in config:
                        config['prevent_sleep'] = False
                    if 'restore_volume' not in config:
                        config['restore_volume'] = False
                    if 'restore_volume_level' not in config:
                        config['restore_volume_level'] = 50
                    if 'stream_a' not in config:
                        config['stream_a'] = {}
                    if 'stream_b' not in config:
                        config['stream_b'] = {}
                    return config
            
            # If we get here, config file doesn't exist - create a new one with defaults
            config = {
                'transparent_window': True,
                'prevent_sleep': False,
                'restore_volume': False,
                'restore_volume_level': 50,
                'last_dir': os.path.expanduser("~"),
                'window_position': {'x': 100, 'y': 100},
                'stream_a': {},
                'stream_b': {}
            }
            # Ensure the directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            # Save the default config
            self.save_config(config)
            return config
            
        except Exception as e:
            print(f"Error loading config: {e}")
            # Return minimal default config
            return {
                'transparent_window': True,
                'prevent_sleep': False,
                'restore_volume': False,
                'restore_volume_level': 50,
                'last_dir': os.path.expanduser("~"),
                'window_position': {'x': 100, 'y': 100},
                'stream_a': {},
                'stream_b': {}
            }

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better styling support
    app.setStyleSheet(STYLESHEET)  # Apply stylesheet to the entire application
    window = ShittySoundLooper()
    window.show()
    sys.exit(app.exec())