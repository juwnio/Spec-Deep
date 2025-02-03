import customtkinter as ctk

class CompletionDialog:
    def __init__(self, parent):
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Task Complete")
        
        # Center the dialog
        window_width = 300
        window_height = 150
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.dialog.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Make it modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog stay on top
        self.dialog.attributes('-topmost', True)
        
        # Add completion message
        message = ctk.CTkLabel(
            self.dialog,
            text="✅ Task Successfully Completed!",
            font=("Segoe UI", 16, "bold")
        )
        message.pack(pady=20)
        
        # Add OK button
        ok_button = ctk.CTkButton(
            self.dialog,
            text="OK",
            command=self.dialog.destroy,
            width=100
        )
        ok_button.pack(pady=10)
        
        # Add keyboard binding for OK
        self.dialog.bind('<Return>', lambda e: self.dialog.destroy())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Prevent closing without using buttons
        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)
        
        # Focus the OK button
        ok_button.focus_set()
