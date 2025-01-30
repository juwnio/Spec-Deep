import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
from ollama import Client
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import time
from queue import Queue
import re

class LoadingAnimation:
    def __init__(self, label: ttk.Label):
        self.label = label
        self.dots = 0
        self.running = False
        self._after_id = None
    
    def start(self):
        self.running = True
        self._animate()
    
    def stop(self):
        self.running = False
        if self._after_id:
            self.label.after_cancel(self._after_id)
        self.label.configure(text="")
    
    def _animate(self):
        if not self.running:
            return
        self.dots = (self.dots + 1) % 4
        self.label.configure(text="Processing" + "." * self.dots)
        self._after_id = self.label.after(300, self._animate)

class OllamaGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Ollama Chat Interface")
        self.root.geometry("800x600")
        
        # Configure main window
        self.root.configure(bg='#2b2b2b')
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Model selection
        self.model_frame = ttk.Frame(root)
        self.model_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Label(self.model_frame, text="Model:").pack(side=tk.LEFT, padx=5)
        self.model_var = tk.StringVar(value="deepseek-r1:1.5b")
        self.model_entry = ttk.Entry(self.model_frame, textvariable=self.model_var)
        self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Add connection status indicator
        self.status_label = ttk.Label(self.model_frame, text="⚫ Disconnected")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Create display frames
        display_frame = ttk.Frame(root)
        display_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_columnconfigure(1, weight=1)
        display_frame.grid_rowconfigure(1, weight=1)

        # Thoughts display
        ttk.Label(display_frame, text="Thoughts:").grid(row=0, column=0, sticky="w", padx=5)
        self.thoughts_display = scrolledtext.ScrolledText(display_frame, wrap=tk.WORD, bg='#1e1e1e', fg='#a8c9ff', height=10)
        self.thoughts_display.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Actions display
        ttk.Label(display_frame, text="Actions:").grid(row=0, column=1, sticky="w", padx=5)
        self.actions_display = scrolledtext.ScrolledText(display_frame, wrap=tk.WORD, bg='#1e1e1e', fg='#ffffff', height=10)
        self.actions_display.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        # Input frame
        input_frame = ttk.Frame(root)
        input_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.input_field = ttk.Entry(input_frame)
        self.input_field.grid(row=0, column=0, padx=5, sticky="ew")
        self.input_field.bind("<Return>", self.send_message)
        
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=5)
        
        # Add loading indicator
        self.loading_label = ttk.Label(input_frame, text="")
        self.loading_label.grid(row=0, column=3, padx=5)
        self.loading_animation = LoadingAnimation(self.loading_label)
        
        # Initialize Ollama client
        self.client = Client(host='http://localhost:11434')
        
        # Add new instance variables
        self.response_buffer = []
        self.buffer_lock = threading.Lock()
        self.update_queue = Queue()
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.last_input_time = 0
        self.is_connected = False
        
        # Start update loop and connection check
        self.check_connection()
        self.start_update_loop()
        
        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
    
    def cleanup(self) -> None:
        """Clean up resources before closing."""
        self.loading_animation.stop()
        self.thread_pool.shutdown(wait=False)
        self.root.destroy()
    
    def check_connection(self) -> None:
        """Check Ollama server connection status."""
        try:
            self.client.list()
            if not self.is_connected:
                self.status_label.config(text="🟢 Connected")
                self.is_connected = True
        except Exception:
            self.status_label.config(text="⚫ Disconnected")
            self.is_connected = False
        self.root.after(5000, self.check_connection)
    
    def send_message(self, event=None) -> None:
        """Handle message sending with debouncing."""
        current_time = time.time()
        if current_time - self.last_input_time < 0.1:  # 100ms debouncing
            return
        
        user_input = self.input_field.get().strip()
        if not user_input:
            return
        
        self.last_input_time = current_time
        self.input_field.delete(0, tk.END)
        self.actions_display.insert(tk.END, f"You: {user_input}\n\n")
        self.actions_display.see(tk.END)
        
        if not self.is_connected:
            self.actions_display.insert(tk.END, "Error: Not connected to Ollama server\n\n")
            return
        
        self.loading_animation.start()
        self.send_button.configure(state="disabled")
        self.thread_pool.submit(self.get_response, user_input)
    
    def get_response(self, prompt: str) -> None:
        try:
            model = self.model_var.get()
            current_thought = []
            in_thought = False
            
            for chunk in self.client.generate(model=model, prompt=prompt, stream=True):
                if chunk.get('response'):
                    text = chunk['response']
                    
                    # Handle think tags with regex
                    if '<think>' in text:
                        in_thought = True
                    
                    if in_thought:
                        current_thought.append(text.replace('<think>', '').replace('</think>', ''))
                        if '</think>' in text:
                            in_thought = False
                            thought_text = ''.join(current_thought)
                            self.queue_update('thought', thought_text)
                            current_thought = []
                    else:
                        self.queue_update('action', text)
            
            self.queue_update('newline', '')
            
        except Exception as e:
            self.queue_update('error', f"Error: {str(e)}\n\n")
        finally:
            self.root.after(0, self._reset_ui_state)
    
    def _reset_ui_state(self) -> None:
        """Reset UI elements after processing."""
        self.loading_animation.stop()
        self.send_button.configure(state="normal")
    
    def queue_update(self, update_type: str, text: str) -> None:
        """Queue updates for batch processing."""
        self.update_queue.put((update_type, text))
    
    def start_update_loop(self) -> None:
        """Process queued updates periodically."""
        while not self.update_queue.empty():
            update_type, text = self.update_queue.get()
            if update_type == 'thought':
                self.thoughts_display.insert(tk.END, text)
                self.thoughts_display.see(tk.END)
            elif update_type == 'action':
                cleaned_text = re.sub(r'</think>|<think>|Assistant:', '', text)
                if cleaned_text.strip():
                    self.actions_display.insert(tk.END, cleaned_text)
                    self.actions_display.see(tk.END)
            elif update_type == 'error':
                self.actions_display.insert(tk.END, text)
                self.actions_display.see(tk.END)
            elif update_type == 'newline':
                self.thoughts_display.insert(tk.END, "\n\n")
                self.actions_display.insert(tk.END, "\n\n")
        
        self.root.after(50, self.start_update_loop)  # Run every 50ms

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()
