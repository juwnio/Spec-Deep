import tkinter as tk
from tkinter import scrolledtext, ttk
import subprocess
import threading
from ollama import Client
import sys

class OllamaGUI:
    def __init__(self, root):
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
        
        # Initialize Ollama client
        self.client = Client(host='http://localhost:11434')
        
    def send_message(self, event=None):
        user_input = self.input_field.get()
        if not user_input.strip():
            return
            
        self.input_field.delete(0, tk.END)
        self.actions_display.insert(tk.END, f"You: {user_input}\n\n")
        self.actions_display.see(tk.END)
        
        # Create a thread for the API call
        thread = threading.Thread(target=self.get_response, args=(user_input,))
        thread.daemon = True
        thread.start()
    
    def get_response(self, prompt):
        try:
            model = self.model_var.get()
            current_thought = ""
            in_thought = False
            
            for chunk in self.client.generate(model=model, prompt=prompt, stream=True):
                if chunk.get('response'):
                    text = chunk['response']
                    
                    # Handle opening think tag
                    if '<think>' in text:
                        in_thought = True
                        current_thought = ""
                    
                    # Handle closing think tag
                    if '</think>' in text and in_thought:
                        in_thought = False
                        self.root.after(1, self.append_to_chat, f"<think>{current_thought}</think>")
                    
                    # Accumulate thought or append action
                    if in_thought:
                        current_thought += text.replace('<think>', '')
                    else:
                        self.root.after(1, self.append_to_chat, text)
                    
                    self.root.update()
            
            self.thoughts_display.insert(tk.END, "\n\n")
            self.actions_display.insert(tk.END, "\n\n")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}\n\n"
            self.actions_display.insert(tk.END, error_msg)
            self.actions_display.see(tk.END)
    
    def append_to_chat(self, text):
        # Process think tags
        if '<think>' in text:
            thought = text.split('<think>')[1].split('</think>')[0] if '</think>' in text else text.split('<think>')[1]
            self.thoughts_display.insert(tk.END, thought)
            self.thoughts_display.see(tk.END)
        else:
            # Clean up any leftover think tags and Assistant prefixes
            text = text.replace('</think>', '').replace('Assistant:', '')
            if text.strip():
                self.actions_display.insert(tk.END, text)
                self.actions_display.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()
