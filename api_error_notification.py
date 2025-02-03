import customtkinter as ctk

class APIErrorNotification:
    def __init__(self, parent):
        self.notification = ctk.CTkToplevel(parent)
        self.notification.title("")
        
        # Make it small and centered
        window_width = 400
        window_height = 100
        screen_width = self.notification.winfo_screenwidth()
        screen_height = self.notification.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.notification.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Remove window decorations
        self.notification.overrideredirect(True)
        self.notification.attributes('-topmost', True)
        
        # Create frame with border
        frame = ctk.CTkFrame(self.notification, border_width=2)
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Error message
        message = ctk.CTkLabel(
            frame,
            text="⚠️ API Key Invalid or Expired",
            font=("Segoe UI", 16, "bold"),
            text_color="red"
        )
        message.pack(pady=10)
        
        # Additional info
        info = ctk.CTkLabel(
            frame,
            text="Please check your API key or generate a new one",
            font=("Segoe UI", 12)
        )
        info.pack(pady=5)
        
        # Auto-close after 5 seconds
        self.notification.after(5000, self.close)
        
        # Click anywhere to dismiss
        frame.bind("<Button-1>", lambda e: self.close())
        message.bind("<Button-1>", lambda e: self.close())
        info.bind("<Button-1>", lambda e: self.close())
    
    def close(self):
        self.notification.destroy()
