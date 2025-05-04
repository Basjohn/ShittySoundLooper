import tkinter as tk
from tkinter import filedialog
import pygame
import os
import json
from pathlib import Path
import customtkinter as ctk
import sys
import numpy as np
import wave
import array
import math
import tempfile
import webbrowser
from PIL import Image, ImageTk
import threading
if sys.platform == 'win32':
    import win32api
    import win32con
    import pystray
    import ctypes

class ShittySoundLooper:
    def __init__(self):
        # Initialize pygame mixer with higher quality settings
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
        # Initialize variables
        self.base_path = self._get_base_path()
        self.config_file = self.base_path / "config.json"
        self.last_dir = os.path.expanduser("~")
        self.loops_dir = os.path.join(self.base_path, "loops")
        self.audio_file = None
        self.playing = False
        self.sound = None
        self.temp_file = None
        self.tray_icon = None
        self.tray_thread = None  # Thread for the system tray
        self.hidden = False  # Track if window is hidden
        
        # Create loops directory if it doesn't exist
        if not os.path.exists(self.loops_dir):
            try:
                os.makedirs(self.loops_dir)
            except:
                # If we can't create it, default to user's home
                self.loops_dir = os.path.expanduser("~")
        
        # Create main window
        self.window = ctk.CTk()
        self.window.title("Shitty Sound Looper")
        
        # Make window resizable and set minimum size - 25px wider
        self.window.resizable(True, True)
        self.window.minsize(650, 231)  # 50px wider (previously 600)
        
        # Center window
        self.center_window(650, 231)
        
        # Load icon - simpler approach for better compatibility
        self.icon_path = self._get_icon_path()
        if self.icon_path:
            try:
                self.window.iconbitmap(self.icon_path)
                if sys.platform == 'win32':
                    try:
                        myappid = 'shitty.sound.looper'
                        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                    except Exception as e:
                        print(f"Error setting app ID: {e}")
            except Exception as e:
                print(f"Error setting window icon: {e}")
        
        # Create UI elements
        self.create_ui()
        
        # Load configuration
        self.load_config()
        
        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Initialize system tray
        self.init_system_tray()
    
    def _get_base_path(self):
        """Get the base path for the application resources"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return Path(os.path.dirname(sys.executable))
        else:
            # Running as script
            return Path(os.path.dirname(os.path.abspath(__file__))).parent
    
    def _get_icon_path(self):
        """Get the path to the icon file, with better handling for PyInstaller bundles"""
        # Check for icon in resources directory
        icon_path = os.path.join(self.base_path, "resources", "MoonIcon.ico")
        if os.path.exists(icon_path):
            return icon_path
            
        # Check for icon in base directory
        icon_path = os.path.join(self.base_path, "MoonIcon.ico")
        if os.path.exists(icon_path):
            return icon_path
            
        # For PyInstaller bundle, extract icon if needed
        if getattr(sys, 'frozen', False):
            try:
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_icon = os.path.join(temp_dir, "SSL_icon.ico")
                
                # If we already have a temp icon, use it
                if os.path.exists(temp_icon):
                    return temp_icon
                    
                # Otherwise, copy the icon from resources
                bundle_icon = os.path.join(self._get_resource_path(), "MoonIcon.ico")
                if os.path.exists(bundle_icon):
                    import shutil
                    shutil.copy2(bundle_icon, temp_icon)
                    return temp_icon
            except Exception as e:
                print(f"Error extracting icon: {e}")
                
        return None
        
    def _get_resource_path(self):
        """Get path to resources, works for dev and PyInstaller"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return os.path.join(sys._MEIPASS, "resources")
        else:
            # Running as script
            return os.path.join(self.base_path, "resources")
    
    def center_window(self, width, height):
        """Center the window on the screen"""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def on_window_close(self):
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Exit")
        dialog.geometry("350x120")
        dialog.attributes('-topmost', True)
        dialog.resizable(False, False)
        
        label = ctk.CTkLabel(dialog, text="Exit or Minimize to Tray?")
        label.pack(pady=20)
        
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=10)
        
        exit_button = ctk.CTkButton(button_frame, text="Exit", command=lambda: self.quit_and_destroy(dialog))
        exit_button.pack(side="left", padx=10)
        
        minimize_button = ctk.CTkButton(button_frame, text="Minimize to Tray", command=lambda: self.minimize_and_destroy(dialog))
        minimize_button.pack(side="right", padx=10)
        
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - dialog.winfo_width()) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        self.window.wait_window(dialog)
        
    def quit_and_destroy(self, dialog):
        dialog.destroy()
        self.safe_quit()
        
    def minimize_and_destroy(self, dialog):
        dialog.destroy()
        self.minimize_to_tray()
        
    def create_ui(self):
        # Main frame to handle layout, matching window background
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # File selection frame
        file_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        file_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)
        
        self.file_entry = ctk.CTkEntry(file_frame, placeholder_text="Select an audio file...")
        self.file_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        browse_button = ctk.CTkButton(file_frame, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=1)
        
        # Controls frame
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        controls_frame.grid_columnconfigure(0, weight=1)
        
        # Buttons & controls row
        self.play_button = ctk.CTkButton(
            controls_frame, 
            text="Play", 
            command=self.play_pause,
            state="disabled"
        )
        self.play_button.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        # Volume control frame
        volume_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        volume_frame.grid(row=0, column=1, sticky="ew")
        volume_frame.grid_columnconfigure(1, weight=1)
        
        volume_label = ctk.CTkLabel(volume_frame, text="Volume:")
        volume_label.grid(row=0, column=0, padx=(10, 5))
        
        self.volume_slider = ctk.CTkSlider(
            volume_frame, 
            from_=0, 
            to=100,
            number_of_steps=100,
            command=self.update_volume
        )
        self.volume_slider.set(50)  # Default to 50%
        self.volume_slider.grid(row=0, column=1, padx=5, sticky="ew")
        
        volume_value = ctk.CTkLabel(volume_frame, text="50%", width=40)
        volume_value.grid(row=0, column=2, padx=(5, 0))
        
        # Link the volume slider to the value label
        def update_volume_label(value):
            volume_value.configure(text=f"{int(value)}%")
            self.update_volume(value)
            
        self.volume_slider.configure(command=update_volume_label)
        
        # About button (right-aligned)
        about_button = ctk.CTkButton(
            controls_frame, 
            text="About", 
            command=self.show_about,
            width=80
        )
        about_button.grid(row=0, column=2, padx=(10, 0), sticky="e")
        
        # Status bar
        status_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        status_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="Ready", 
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w")

    def show_about(self):
        about_dialog = ctk.CTkToplevel(self.window)
        about_dialog.title("About Shitty Sound Looper")
        about_dialog.geometry("400x300")
        about_dialog.attributes('-topmost', True)
        about_dialog.resizable(False, False)
        
        message = "Made for my own shitty sleep, shared freely for yours.\nYou can always donate to my dumbass though or buy my shitty literature."
        label = ctk.CTkLabel(about_dialog, text=message, wraplength=360)
        label.pack(pady=(20, 15))
        
        link_frame = ctk.CTkFrame(about_dialog)
        link_frame.pack(pady=(0, 20))
        
        paypal_button = ctk.CTkButton(
            link_frame,
            text="PayPal",
            command=lambda: webbrowser.open("https://www.paypal.com/donate/?business=UBZJY8KHKKLGC&no_recurring=0&item_name=Why+are+you+doing+this%3F+Are+you+drunk%3F&currency_code=USD"),
            corner_radius=10,
            width=100
        )
        paypal_button.pack(side="left", padx=5)
        
        goodreads_button = ctk.CTkButton(
            link_frame,
            text="Goodreads",
            command=lambda: webbrowser.open("https://www.goodreads.com/book/show/25006763-usu"),
            corner_radius=10,
            width=100
        )
        goodreads_button.pack(side="left", padx=5)
        
        amazon_button = ctk.CTkButton(
            link_frame,
            text="Amazon",
            command=lambda: webbrowser.open("https://www.amazon.com/Usu-Jayde-Ver-Elst-ebook/dp/B00V8A5K7Y"),
            corner_radius=10,
            width=100
        )
        amazon_button.pack(side="left", padx=5)
        
        about_dialog.transient(self.window)
        about_dialog.grab_set()
        
        about_dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - about_dialog.winfo_width()) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - about_dialog.winfo_height()) // 2
        about_dialog.geometry(f"+{x}+{y}")
        
        self.window.wait_window(about_dialog)
        
    def browse_file(self):
        # Determine initial directory
        initial_dir = self.last_dir
        
        # If entry is empty, use loops directory
        if not self.file_entry.get():
            initial_dir = self.loops_dir
            
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            initialdir=initial_dir,
            filetypes=[
                ("Audio Files", "*.wav;*.mp3;*.ogg"),
                ("WAV Files", "*.wav"),
                ("MP3 Files", "*.mp3"),
                ("OGG Files", "*.ogg"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
            
            # Save the last directory
            self.last_dir = os.path.dirname(filename)
            
            # Process the audio file
            self.process_audio(filename)
            
    def process_audio(self, filename):
        if not filename or not os.path.exists(filename):
            return
            
        self.audio_file = filename
        self.status_label.configure(text="Processing audio...")
        
        try:
            # Stop any currently playing sound
            if self.sound:
                self.sound.stop()
                self.playing = False
                self.play_button.configure(text="Play")
            
            # Clear previous temp file if it exists
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.remove(self.temp_file)
                    self.temp_file = None
                except:
                    pass
            
            # Check file extension
            extension = os.path.splitext(filename)[1].lower()
            
            if extension == '.wav':
                processed_file = self.process_wav_with_zero_crossing(filename)
                if processed_file:
                    self.sound = pygame.mixer.Sound(processed_file)
                    self.sound.set_volume(self.volume_slider.get() / 100)
                    self.play_button.configure(state="normal")
            else:
                # For other formats, use pygame directly
                self.sound = pygame.mixer.Sound(filename)
                self.sound.set_volume(self.volume_slider.get() / 100)
                self.status_label.configure(text="Ready (basic mode)")
                self.play_button.configure(state="normal")
                
        except Exception as e:
            print(f"Error processing audio: {e}")
            self.status_label.configure(text=f"Error processing audio")
    
    def process_wav_with_zero_crossing(self, filename):
        """Process a WAV file to create a seamless loop using zero-crossing detection"""
        try:
            # Open the wav file
            with wave.open(filename, 'rb') as wav_file:
                # Get basic file properties
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                # Read all frames
                frames = wav_file.readframes(n_frames)
            
            # Convert frames to numpy array for easier processing
            if sample_width == 2:  # 16-bit audio
                dtype = np.int16
                max_value = 32767
            elif sample_width == 4:  # 32-bit audio
                dtype = np.int32
                max_value = 2147483647
            else:
                dtype = np.int8
                max_value = 127
                
            # Use numpy for more efficient data manipulation
            data = np.frombuffer(frames, dtype=dtype)
            
            # Handle stereo data (just use one channel for zero crossing analysis)
            if n_channels == 2:
                # Take left channel for analysis, but keep both for output
                analysis_data = data[::2]
            else:
                analysis_data = data
            
            def find_zero_crossings(data, start, end):
                """Find zero crossing points within a range"""
                # Optimized zero crossing detection with vectorized operations
                zero_crossings = np.where(np.diff(np.signbit(data[start:end])))[0] + start
                return zero_crossings
            
            # Analyze only a portion of the file for efficiency
            min_loop_seconds = 1.0  # Minimum loop duration in seconds
            min_loop_samples = int(min_loop_seconds * framerate)
            
            # Determine analysis range
            analysis_length = min(len(analysis_data), 1000000)  # Cap analysis length for performance
            
            # Find a good loop point in the first section of the file
            start_range = min(int(analysis_length * 0.1), 10000)
            start_crossings = find_zero_crossings(analysis_data, 0, start_range)
            
            # Find a good loop point near the end of the analysis section
            end_range_start = max(start_range + min_loop_samples, int(analysis_length * 0.7))
            end_range_end = analysis_length
            end_crossings = find_zero_crossings(analysis_data, end_range_start, end_range_end)
            
            if len(start_crossings) == 0 or len(end_crossings) == 0:
                # Fall back to simple positions if no good zero crossings found
                loop_start = 0
                loop_end = analysis_length
            else:
                # Choose zero crossings with similar amplitude and slope
                best_diff = float('inf')
                loop_start = start_crossings[0]
                loop_end = end_crossings[0]
                
                # Only check a subset of crossings for performance
                start_check = start_crossings[:min(50, len(start_crossings))]
                end_check = end_crossings[:min(50, len(end_crossings))]
                
                for start_pos in start_check:
                    for end_pos in end_check:
                        # Look at samples right before the zero crossings
                        try:
                            start_val = analysis_data[start_pos-1]
                            end_val = analysis_data[end_pos-1]
                            diff = abs(start_val - end_val)
                            
                            if diff < best_diff:
                                best_diff = diff
                                loop_start = start_pos
                                loop_end = end_pos
                        except IndexError:
                            continue
            
            # Scale back to stereo if needed
            if n_channels == 2:
                loop_start *= 2
                loop_end *= 2
            
            # Create the looped data
            loop_length = loop_end - loop_start
            loop_data = data[loop_start:loop_end]
            
            # Create a temporary file for the processed audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp:
                self.temp_file = temp.name
            
            # Save the processed data to the temp file
            with wave.open(self.temp_file, 'wb') as wav_file:
                wav_file.setnchannels(n_channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(framerate)
                
                if loop_data.dtype != dtype:
                    loop_data = loop_data.astype(dtype)
                
                wav_file.writeframes(loop_data.tobytes())
            
            # Update UI to show loop duration
            loop_duration = loop_length / (framerate * n_channels * (sample_width / 2))
            self.status_label.configure(text=f"Loop Duration: {loop_duration:.2f} seconds")
            
            return self.temp_file
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            self.status_label.configure(text=f"Error: {str(e)}")
            return None
    
    def play_pause(self):
        try:
            if not self.playing:
                if self.sound:
                    self.sound.play(-1)  # Loop indefinitely
                    self.playing = True
                    self.play_button.configure(text="Pause")
                    self.status_label.configure(text="Playing")
            else:
                if self.sound:
                    self.sound.stop()
                    self.playing = False
                    self.play_button.configure(text="Play")
                    self.status_label.configure(text="Paused")
        except Exception as e:
            print(f"Error playing/pausing: {e}")
            self.status_label.configure(text=f"Error: {str(e)}")
    
    def toggle_pause(self):
        """Toggle audio playback pause/play state"""
        if self.sound:
            if self.playing:
                self.sound.stop()
                self.playing = False
            else:
                self.sound.play(-1)  # Loop indefinitely
                self.playing = True
                
    def update_volume(self, value):
        if self.sound:
            self.sound.set_volume(float(value) / 100)
            
    def safe_quit(self):
        """Safely quit the application, handling all cleanup"""
        try:
            # Save user configuration first
            self.save_config()
            
            # Stop audio playback
            if self.sound:
                self.sound.stop()
                self.sound = None
            
            # Clean up temporary files
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.remove(self.temp_file)
                except Exception as e:
                    print(f"Error cleaning up temp file: {e}")
            
            # Stop the system tray icon if it exists
            if self.tray_icon:
                try:
                    self.tray_icon.stop()
                except Exception as e:
                    print(f"Error stopping tray icon: {e}")
            
            # Quit pygame mixer
            pygame.mixer.quit()
            
            # Destroy main window
            self.window.destroy()
            
        except Exception as e:
            print(f"Error in quit: {e}")
            # Force exit if normal shutdown fails
            try:
                self.window.destroy()
            except:
                pass
            os._exit(0)
    
    # Rename quit to avoid confusion and potential naming conflicts
    def quit(self):
        self.safe_quit()
            
    def minimize_to_tray(self):
        """Hide the window and show the system tray icon if not already visible"""
        if not self.tray_icon:
            self.init_system_tray()
        self.window.withdraw()  # Hide the window
        self.hidden = True
    
    def restore_window(self):
        """Restore the window from the system tray"""
        try:
            if self.hidden:
                self.window.deiconify()
                self.window.state('normal')  # Ensure it's not minimized
                self.window.lift()
                self.window.focus_force()
                self.hidden = False
                
                # Additional fixes for Windows focus issues
                if sys.platform == 'win32':
                    try:
                        # Ensure window is visible and focused
                        self.window.attributes('-topmost', True)
                        self.window.update()
                        self.window.attributes('-topmost', False)
                    except Exception as e:
                        print(f"Error focusing window: {e}")
        except Exception as e:
            print(f"Error restoring window: {e}")
    
    def init_system_tray(self):
        """Initialize the system tray icon using pystray"""
        if not sys.platform == 'win32':
            return
            
        try:
            if not self.icon_path:
                print("Icon file not found")
                return
                
            # Create the icon for the system tray
            icon_image = Image.open(self.icon_path)
            
            # Define the menu for the system tray
            def on_play_pause(icon, item):
                # Schedule action on main thread
                self.window.after(0, self.toggle_pause)
                
            def on_restore(icon, item):
                # Schedule action on main thread
                self.window.after(0, self.restore_window)
                
            def on_quit(icon, item):
                # Schedule quit on main thread
                self.window.after(0, self.safe_quit)
            
            # Create the menu
            menu = pystray.Menu(
                pystray.MenuItem("Play/Pause", on_play_pause),
                pystray.MenuItem("Restore", on_restore),
                pystray.MenuItem("Quit", on_quit)
            )
            
            # Create the icon
            self.tray_icon = pystray.Icon("ssl_tray", icon_image, "Shitty Sound Looper", menu)
            
            # Handle left-click on icon
            def setup(icon):
                icon.visible = True
                
                # Define a custom click handler
                def on_click(icon, button, pressed):
                    if button == pystray.mouse.Button.left and pressed:
                        # Schedule restore to run on the main thread
                        self.window.after(0, self.restore_window)
                
                # Set the click handler
                icon._click_cb = on_click
            
            # Start the icon in a separate thread
            self.tray_thread = threading.Thread(target=self.tray_icon.run, kwargs={'setup': setup})
            self.tray_thread.daemon = True  # So it doesn't block app exit
            self.tray_thread.start()
            
        except Exception as e:
            print(f"Error initializing system tray: {e}")
    
    def save_config(self):
        try:
            config = {
                'last_dir': self.last_dir,
                'last_file': self.audio_file if self.audio_file else '',
                'volume': self.volume_slider.get()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.last_dir = config.get('last_dir', os.path.expanduser("~"))
                    volume = config.get('volume', 50)
                    self.volume_slider.set(volume)
                    last_file = config.get('last_file', '')
                    if last_file and os.path.exists(last_file):
                        self.file_entry.delete(0, tk.END)
                        self.file_entry.insert(0, last_file)
                        self.audio_file = last_file
                        self.window.after(500, lambda: self.process_audio(last_file))
            else:
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.last_dir = os.path.expanduser("~")
            self.save_config()
            
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = ShittySoundLooper()
    app.run()
