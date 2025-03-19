import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess
import pyttsx3
import os
import signal

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Shared file for mode communication
MODE_FILE = "mode.txt"

# Improved GUI with text-to-speech feedback and fixes
class GestureControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GesturePilot - Gesture Control System")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)  # Minimum window size

        # Initialize gesture control process
        self.gesture_process = None  # Fix: Initialize gesture_process

        # Load background image
        self.bg_image = Image.open("background1.png")  # Replace with your image path
        self.bg_image_tk = ImageTk.PhotoImage(self.bg_image)

        # Create a canvas for the background image
        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor="nw")

        # Bind the canvas to window resize events
        self.canvas.bind("<Configure>", self.resize_background)

        # Header with project name
        self.header = self.canvas.create_text(
            400, 50,  # Position
            text="GesturePilot",
            font=("Arial", 24, "bold"),
            fill="white"
        )

        # Subheader
        self.subheader = self.canvas.create_text(
            400, 100,  # Position
            text="Control Your System with Hand Gestures",
            font=("Arial", 14),
            fill="white"
        )

        # Top Frame for Start and Stop buttons
        self.top_frame = tk.Frame(self.canvas, bg="", bd=0)  # Transparent background
        self.top_frame.place(relx=0.5, rely=0.2, anchor="center")  # Position at the top

        # Start and Stop buttons
        self.start_button = tk.Button(
            self.top_frame,
            text="Start",
            command=lambda: self.set_mode("start", "Start"),
            bg="teal",  # Set background color
            fg="black",  # Set text color to black
            font=("Arial", 20, "bold"),  # Set font
            activebackground="teal",  # Set active background color
            activeforeground="black",  # Set active text color
            bd=0,  # Remove border
            highlightthickness=0  # Remove highlight
        )
        self.start_button.grid(row=0, column=0, padx=10, pady=10)

        self.stop_button = tk.Button(
            self.top_frame,
            text="Stop",
            command=lambda: self.set_mode("stop", "Stop"),
            bg="red",  # Set background color
            fg="black",  # Set text color to black
            font=("Arial", 20, "bold"),  # Set font
            activebackground="red",  # Set active background color
            activeforeground="black",  # Set active text color
            bd=0,  # Remove border
            highlightthickness=0  # Remove highlight
        )
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)

        # Bottom Frame for other buttons
        self.bottom_frame = tk.Frame(self.canvas, bg="", bd=0)  # Transparent background
        self.bottom_frame.place(relx=0.5, rely=0.8, anchor="center")  # Position at the bottom

        # Buttons for Modes
        self.modes = [
            ("Brightness", "brightness", "#4C566A", ("Arial", 12, "bold")),
            ("Volume", "volume", "#4C566A", ("Arial", 12, "bold")),
            ("Mouse", "mouse", "#4C566A", ("Arial", 12, "bold")),
            ("Zoom", "zoom", "#4C566A", ("Arial", 12, "bold")),
            ("Screenshot", "screenshot", "#4C566A", ("Arial", 12, "bold")),
            ("Media", "media", "#4C566A", ("Arial", 12, "bold")),
            ("Scroll", "scroll", "#4C566A", ("Arial", 12, "bold")),  # New Scroll feature
            ("App Switcher", "switcher", "#4C566A", ("Arial", 12, "bold"))  # New App Switcher feature
        ]

        for i, (text, mode, color, font) in enumerate(self.modes):
            button = tk.Button(
                self.bottom_frame,
                text=text,
                command=lambda m=mode, t=text: self.set_mode(m, t),
                bg=color,  # Set background color
                fg="black",  # Set text color to black
                font=font,  # Set font
                activebackground=color,  # Set active background color
                activeforeground="black",  # Set active text color
                bd=0,  # Remove border
                highlightthickness=0  # Remove highlight
            )
            button.grid(row=i // 4, column=i % 4, padx=10, pady=10)

        # Status Bar (bottom left corner)
        self.status_bar = tk.Label(self.canvas, text="Ready", font=("Arial", 12), bg="white", fg="black", anchor=tk.W)
        self.status_bar.place(relx=0.02, rely=0.95, anchor="sw")  # Bottom left corner

    def resize_background(self, event):
        """Resize the background image dynamically."""
        # Get the new window size
        new_width = event.width
        new_height = event.height

        # Resize the background image
        resized_bg = self.bg_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.bg_image_tk = ImageTk.PhotoImage(resized_bg)

        # Update the canvas background
        self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor="nw")

    def set_mode(self, mode, text):
        # Update status bar
        self.status_bar.config(text=f"Mode set to: {text}")

        # Provide text-to-speech feedback
        self.speak(f"{text} mode selected")

        # Handle Start and Stop buttons
        if mode == "start":
            self.start_gesture_control()
        elif mode == "stop":
            self.stop_gesture_control()
        else:
            # Write the selected mode to the shared file
            with open(MODE_FILE, "w") as f:
                f.write(mode)

    def start_gesture_control(self):
        """Start the gesture control system as a subprocess."""
        if self.gesture_process is None:
            self.gesture_process = subprocess.Popen(["python", "project1.py"])
            self.status_bar.config(text="Gesture control system started.")

    def stop_gesture_control(self):
        """Stop the gesture control system."""
        if self.gesture_process is not None:
            self.gesture_process.terminate()
            self.gesture_process = None
            self.status_bar.config(text="Gesture control system stopped.")

    def speak(self, text):
        """Convert text to speech."""
        engine.say(text)
        engine.runAndWait()

if __name__ == "__main__":
    # Initialize the mode file
    with open(MODE_FILE, "w") as f:
        f.write("brightness")  # Default mode

    root = tk.Tk()
    app = GestureControlApp(root)
    root.mainloop()