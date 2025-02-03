import customtkinter as ctk
import sys

class RateLimitDialog:
    def __init__(self, parent, countdown_seconds=600):
        self.dialog = ctk.CTkToplevel(parent)
        self.parent = parent
        self.dialog.title("Rate Limit Exceeded")
        
        # Center the dialog
        window_width = 400
        window_height = 300  # Increased height for new elements
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.dialog.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Make it modal and stay on top
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.attributes('-topmost', True)
        
        # Warning message
        warning = ctk.CTkLabel(
            self.dialog,
            text="⚠️ Rate Limit Exceeded",
            font=("Segoe UI", 20, "bold")
        )
        warning.pack(pady=(20, 10))
        
        self.message = ctk.CTkLabel(
            self.dialog,
            text="Current model's rate limit reached.\nChoose an option:",
            font=("Segoe UI", 14)
        )
        self.message.pack(pady=5)
        
        # Timer label
        self.timer_label = ctk.CTkLabel(
            self.dialog,
            text="",
            font=("Segoe UI", 16, "bold")
        )
        self.timer_label.pack(pady=10)
        
        # Model selection frame
        model_frame = ctk.CTkFrame(self.dialog)
        model_frame.pack(pady=10, padx=20, fill="x")
        
        model_label = ctk.CTkLabel(
            model_frame,
            text="Switch to model:",
            font=("Segoe UI", 12)
        )
        model_label.pack(pady=5)
        
        # Model buttons
        for model_name in ["LLaMA Spec", "LLaMA Versatile", "DeepSeek"]:
            btn = ctk.CTkButton(
                model_frame,
                text=f"Switch to {model_name}",
                command=lambda m=model_name: self.switch_model(m),
                font=("Segoe UI", 12)
            )
            btn.pack(pady=2, padx=10, fill="x")
        
        # Exit button
        exit_btn = ctk.CTkButton(
            self.dialog,
            text="Close Program",
            command=self.exit_program,
            font=("Segoe UI", 12),
            fg_color="red",
            hover_color="darkred"
        )
        exit_btn.pack(pady=10)
        
        # Start countdown
        self.remaining_time = countdown_seconds
        self.update_timer()
        
        # Prevent closing with X button
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def switch_model(self, model_name):
        """Switch to a different model and close dialog"""
        # Get parent's model selector and change model
        if hasattr(self.parent, 'model_selector'):
            self.parent.model_selector.model_var.set(model_name)
        self.dialog.destroy()
    
    def exit_program(self):
        """Safely exit the program"""
        self.parent.quit()
        sys.exit(0)
    
    def update_timer(self):
        if self.remaining_time > 0:
            minutes = self.remaining_time // 60
            seconds = self.remaining_time % 60
            self.timer_label.configure(text=f"Time until current model reset: {minutes:02d}:{seconds:02d}")
            self.remaining_time -= 1
            self.dialog.after(1000, self.update_timer)
        else:
            self.dialog.destroy()
