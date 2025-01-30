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
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg='#1e1e1e', fg='#ffffff')
        self.chat_display.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
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
        self.chat_display.insert(tk.END, f"You: {user_input}\n\n")
        self.chat_display.see(tk.END)
        
        # Create a thread for the API call
        thread = threading.Thread(target=self.get_response, args=(user_input,))
        thread.daemon = True
        thread.start()
    
    def get_response(self, prompt):
        try:
            model = self.model_var.get()
            self.chat_display.insert(tk.END, "Assistant: ")
            
            for chunk in self.client.generate(model=model, prompt=prompt, stream=True):
                if chunk.get('response'):
                    # Stream each character immediately
                    self.root.after(1, self.append_to_chat, chunk['response'])
                    # Small delay to allow GUI to update
                    self.root.update()
            
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.see(tk.END)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}\n\n"
            self.root.after(1, self.chat_display.insert, tk.END, error_msg)
            self.root.after(1, self.chat_display.see, tk.END)
    
    def append_to_chat(self, text):
        # Clean up any think tags or duplicate Assistant prefixes
        text = text.replace('<think>', '').replace('</think>', '')
        text = text.replace('Assistant:', '')
        self.chat_display.insert(tk.END, text)
        self.chat_display.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()
