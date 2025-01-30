import tkinter as tk
from tkinter import scrolledtext, ttk
from ..services.groq_service import GroqService
from ..services.ollama_service import OllamaService
from ..services.screenshot_service import ScreenshotService
from ..utils.text_utils import TextUtils
# ...existing imports...

class OllamaGUI:
    def __init__(self, root: tk.Tk) -> None:
        # ...existing init code...
        
        # Split thoughts frame into two parts
        thoughts_frame = ttk.Frame(display_frame)
        thoughts_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        thoughts_frame.grid_rowconfigure(0, weight=1)
        thoughts_frame.grid_rowconfigure(1, weight=1)
        
        self.thoughts_display = scrolledtext.ScrolledText(
            thoughts_frame, wrap=tk.WORD, bg='#1e1e1e', fg='#a8c9ff', height=10
        )
        self.thoughts_display.grid(row=0, column=0, sticky="nsew")
        
        self.vision_display = scrolledtext.ScrolledText(
            thoughts_frame, wrap=tk.WORD, bg='#1e1e1e', fg='#ff9e64', height=10
        )
        self.vision_display.grid(row=1, column=0, sticky="nsew")
        
        # Initialize services
        self.groq_service = GroqService()
        self.screenshot_service = ScreenshotService()
        
    async def process_input(self, user_input: str) -> None:
        try:
            # Take screenshot and analyze
            screenshot = self.screenshot_service.capture_and_encode()
            context = TextUtils.read_context("context.txt")
            
            # Get vision analysis
            vision_response = await self.groq_service.analyze_image(screenshot, context)
            self.vision_display.insert(tk.END, f"Vision Analysis:\n{vision_response}\n\n")
            
            # Combine with user input and context2
            context2 = TextUtils.read_context("context2.txt")
            combined_prompt = f"{context2}\n\nUser Input: {user_input}\n\nVision Analysis: {vision_response}"
            
            # Send to Ollama
            self.get_response(combined_prompt)
            
        except Exception as e:
            self.queue_update('error', f"Error: {str(e)}\n\n")
