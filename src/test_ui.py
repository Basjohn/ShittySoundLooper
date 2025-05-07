import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import os

# Define custom dark theme colors
DARK_THEME = {
    "bg_color": "#232323",        # 20% brighter background
    "fg_color": "#F5F5F5",        # Off-white for text
    "button_color": "#2D2D2D",    # Dark gray for buttons
    "hover_color": "#3D3D3D",     # Slightly lighter gray for hover states
    "title_bar_bg": "#333333",    # Medium gray for custom title bar
    "close_button_bg": "#444444", # Lighter gray for close button
    "window_border": "#FFFFFF",   # White for window border
    "divider_line": "#FFFFFF"     # White for divider line
}

class TestApp:
    def __init__(self):
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Create main window
        self.window = ctk.CTk()
        self.window.title("Test UI")
        # Hide the default title bar
        self.window.overrideredirect(True)
        
        # Set window size
        self.window.minsize(490, 350)
        
        # Center window
        self.center_window(490, 350)
        
        # Create UI
        self.create_ui()
        
    def center_window(self, width, height):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _start_window_drag(self, event):
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def _stop_window_drag(self, event):
        self.is_dragging = False
    
    def _on_window_drag(self, event):
        if self.is_dragging:
            x = self.window.winfo_x() + (event.x - self.drag_start_x)
            y = self.window.winfo_y() + (event.y - self.drag_start_y)
            self.window.geometry(f"+{x}+{y}")
    
    def create_ui(self):
        # Create a border frame with white background
        border_frame = ctk.CTkFrame(self.window, fg_color=DARK_THEME["window_border"], corner_radius=0)
        border_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Create an inner frame with the app's background color (3px border effect)
        inner_frame = ctk.CTkFrame(border_frame, fg_color=DARK_THEME["bg_color"], corner_radius=0)
        inner_frame.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Create custom title bar
        title_bar = ctk.CTkFrame(inner_frame, fg_color=DARK_THEME["title_bar_bg"], height=36, corner_radius=0)
        title_bar.pack(fill="x", padx=0, pady=0)
        
        # Bind title bar for window dragging
        title_bar.bind("<ButtonPress-1>", self._start_window_drag)
        title_bar.bind("<ButtonRelease-1>", self._stop_window_drag)
        title_bar.bind("<B1-Motion>", self._on_window_drag)
        
        # Title in the center
        title_label = ctk.CTkLabel(title_bar, text="Test UI", text_color="white", font=("Arial", 14, "bold"))
        title_label.pack(side="left", expand=True, fill="both")
        
        # Close button (smaller and lighter gray square)
        close_button = ctk.CTkButton(
            title_bar, 
            text="✕", 
            command=self.window.destroy,
            width=30,
            height=30,
            corner_radius=0,
            fg_color=DARK_THEME["close_button_bg"],
            hover_color=DARK_THEME["hover_color"]
        )
        close_button.pack(side="right", padx=3, pady=3)
        
        # Add a white horizontal divider line below the title bar
        divider = ctk.CTkFrame(inner_frame, fg_color=DARK_THEME["divider_line"], height=2, corner_radius=0)
        divider.pack(fill="x", padx=0, pady=0)
        
        # Main content frame
        main_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left side frame for buttons
        left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        
        # File entry at the top
        file_entry = ctk.CTkEntry(main_frame, placeholder_text="Select an audio file...")
        file_entry.pack(side="top", fill="x", pady=(0, 10))
        
        # Browse button on the left
        browse_button = ctk.CTkButton(left_frame, text="Browse", command=lambda: None)
        browse_button.pack(fill="x", pady=(0, 10))
        
        # Play button below browse
        play_button = ctk.CTkButton(
            left_frame, 
            text="Play", 
            command=lambda: None
        )
        play_button.pack(fill="x", pady=(0, 10))
        
        # Volume control frame
        volume_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        volume_frame.pack(fill="x", pady=(0, 10))
        
        volume_label = ctk.CTkLabel(volume_frame, text="Volume:")
        volume_label.pack(side="left", padx=(0, 5))
        
        volume_slider = ctk.CTkSlider(
            volume_frame, 
            from_=0, 
            to=100,
            number_of_steps=100
        )
        volume_slider.set(50)
        volume_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        volume_value = ctk.CTkLabel(volume_frame, text="50%", width=40)
        volume_value.pack(side="left", padx=(5, 0))
        
        # Bottom frame for ? button and moon icon side by side
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        # About button (?) on the left
        about_button = ctk.CTkButton(
            bottom_frame, 
            text="?", 
            command=lambda: None,
            width=40,
            height=40
        )
        about_button.pack(side="left", padx=(0, 10))
        
        # Moon icon placeholder
        moon_label = ctk.CTkLabel(bottom_frame, text="Moon Icon Here", width=120, height=120)
        moon_label.pack(side="left")
    
    def run(self):
        # Force window to be on top initially to ensure it's visible
        self.window.attributes('-topmost', True)
        self.window.update()
        self.window.attributes('-topmost', False)
        
        # Force focus to the window
        self.window.focus_force()
        self.window.lift()
        
        # Start the main event loop
        self.window.mainloop()

if __name__ == "__main__":
    app = TestApp()
    app.run()
