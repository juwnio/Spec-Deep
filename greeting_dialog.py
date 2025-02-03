import customtkinter as ctk
import webbrowser
from api_manager import APIManager

class GreetingDialog:
    def __init__(self, parent):
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Welcome to Spec-Drive")
        self.parent = parent
        self.api_manager = APIManager()
        
        # Center and size the dialog
        window_width = 600
        window_height = 400
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.dialog.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Make it modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.attributes('-topmost', True)
        
        # Welcome message
        welcome = ctk.CTkLabel(
            self.dialog,
            text="Welcome to Spec-Drive!",
            font=("Segoe UI", 24, "bold")
        )
        welcome.pack(pady=(20, 10))
        
        # Description
        description = ctk.CTkLabel(
            self.dialog,
            text="Spec-Drive is an AI-powered automation system that uses computer vision\n"
                 "and natural language processing to perform tasks on your computer.\n"
                 "The system watches your screen and executes actions safely and precisely.",
            font=("Segoe UI", 12),
            wraplength=500
        )
        description.pack(pady=10)
        
        # API Key section
        api_frame = ctk.CTkFrame(self.dialog)
        api_frame.pack(pady=20, padx=20, fill="x")
        
        api_label = ctk.CTkLabel(
            api_frame,
            text="Please enter your Groq API Key:",
            font=("Segoe UI", 12)
        )
        api_label.pack(pady=5)
        
        self.api_entry = ctk.CTkEntry(
            api_frame,
            width=400,
            placeholder_text="Enter your API key here"
        )
        self.api_entry.pack(pady=5)
        
        # Get API Key link
        link = ctk.CTkButton(
            api_frame,
            text="Get API Key from Groq",
            command=self.open_groq_website,
            fg_color="transparent",
            text_color=["blue", "lightblue"]
        )
        link.pack(pady=5)
        
        # Continue button
        continue_btn = ctk.CTkButton(
            self.dialog,
            text="Continue",
            command=self.save_and_continue,
            font=("Segoe UI", 12, "bold")
        )
        continue_btn.pack(pady=20)
        
        # Allow closing with X button
        self.dialog.protocol("WM_DELETE_WINDOW", self.handle_close)
    
    def handle_close(self):
        """Handle window close button click"""
        if not self.api_entry.get().strip():
            self.show_error("Please enter an API key before closing")
            return
        self.save_and_continue()

    def open_groq_website(self):
        webbrowser.open("https://console.groq.com/keys")
    
    def save_and_continue(self):
        api_key = self.api_entry.get().strip()
        if not api_key:
            self.show_error("Please enter a valid API key")
            return
            
        if self.api_manager.save_api_key(api_key):
            self.dialog.destroy()
        else:
            self.show_error("Failed to save API key")
    
    def show_error(self, message):
        error_label = ctk.CTkLabel(
            self.dialog,
            text=message,
            text_color="red",
            font=("Segoe UI", 12)
        )
        error_label.pack(pady=5)
        self.dialog.after(2000, error_label.destroy)
