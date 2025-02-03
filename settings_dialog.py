import customtkinter as ctk

class SettingsDialog:
    def __init__(self, parent, api_manager, current_api_key):
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Settings")
        self.api_manager = api_manager
        
        # Center and size the dialog
        window_width = 500
        window_height = 300
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.dialog.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Make it modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Settings header
        header = ctk.CTkLabel(
            self.dialog,
            text="Settings",
            font=("Segoe UI", 20, "bold")
        )
        header.pack(pady=(20, 30))
        
        # API Key section
        api_frame = ctk.CTkFrame(self.dialog)
        api_frame.pack(fill="x", padx=20)
        
        api_label = ctk.CTkLabel(
            api_frame,
            text="API Key:",
            font=("Segoe UI", 12, "bold")
        )
        api_label.pack(pady=(10, 5), padx=10, anchor="w")
        
        self.api_entry = ctk.CTkEntry(
            api_frame,
            width=400,
            show="•"  # Mask API key with dots
        )
        self.api_entry.pack(pady=5, padx=10)
        self.api_entry.insert(0, current_api_key)
        
        # Show/Hide API key button
        self.show_button = ctk.CTkButton(
            api_frame,
            text="Show API Key",
            command=self.toggle_api_visibility,
            width=120
        )
        self.show_button.pack(pady=(5, 10), padx=10, anchor="w")
        
        # Buttons frame
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=self.save_settings,
            font=("Segoe UI", 12)
        )
        save_btn.pack(side="left", padx=10)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            font=("Segoe UI", 12)
        )
        cancel_btn.pack(side="right", padx=10)
        
        self.showing_api = False
    
    def toggle_api_visibility(self):
        self.showing_api = not self.showing_api
        if self.showing_api:
            self.api_entry.configure(show="")
            self.show_button.configure(text="Hide API Key")
        else:
            self.api_entry.configure(show="•")
            self.show_button.configure(text="Show API Key")
    
    def save_settings(self):
        new_api_key = self.api_entry.get().strip()
        if new_api_key:
            if self.api_manager.save_api_key(new_api_key):
                self.show_success()
            else:
                self.show_error("Failed to save API key")
        else:
            self.show_error("API key cannot be empty")
    
    def show_success(self):
        success = ctk.CTkLabel(
            self.dialog,
            text="✓ Settings saved successfully!",
            text_color="green",
            font=("Segoe UI", 12)
        )
        success.pack(pady=5)
        self.dialog.after(2000, success.destroy)
        self.dialog.after(2100, self.dialog.destroy)
    
    def show_error(self, message):
        error = ctk.CTkLabel(
            self.dialog,
            text=f"⚠️ {message}",
            text_color="red",
            font=("Segoe UI", 12)
        )
        error.pack(pady=5)
        self.dialog.after(2000, error.destroy)
