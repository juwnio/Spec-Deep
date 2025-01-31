import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
from ollama import Client
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import time
from queue import Queue
import re
import asyncio
import sys
from src.services.groq_service import GroqService
from src.services.screenshot_service import ScreenshotService
from src.utils.text_utils import TextUtils
import socket
from functools import partial
from src.services.action_executor import ActionExecutor
from src.utils.history_manager import HistoryManager

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
        
        # Add model type selection
        self.model_type_var = tk.StringVar(value="local")
        model_type_frame = ttk.Frame(self.model_frame)
        model_type_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Radiobutton(
            model_type_frame,
            text="Local",
            variable=self.model_type_var,
            value="local",
            command=self.toggle_interface
        ).pack(side=tk.LEFT)
        
        ttk.Radiobutton(
            model_type_frame,
            text="Groq",
            variable=self.model_type_var,
            value="groq",
            command=self.toggle_interface
        ).pack(side=tk.LEFT)

        # Create display frames
        display_frame = ttk.Frame(root)
        display_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_columnconfigure(1, weight=1)
        display_frame.grid_rowconfigure(1, weight=1)

        # Split thoughts frame into two parts
        thoughts_container = ttk.Frame(display_frame)
        thoughts_container.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        thoughts_container.grid_rowconfigure(0, weight=1)
        thoughts_container.grid_rowconfigure(1, weight=1)
        
        # Thoughts display
        ttk.Label(display_frame, text="Thoughts:").grid(row=0, column=0, sticky="w", padx=5)
        self.thoughts_display = scrolledtext.ScrolledText(
            thoughts_container, 
            wrap=tk.WORD, 
            bg='#1e1e1e', 
            fg='#a8c9ff', 
            height=10
        )
        self.thoughts_display.grid(row=0, column=0, sticky="nsew")
        
        # Vision display
        ttk.Label(thoughts_container, text="Vision Analysis:").grid(row=1, column=0, sticky="w", padx=5, pady=(5,0))
        self.vision_display = scrolledtext.ScrolledText(
            thoughts_container, 
            wrap=tk.WORD, 
            bg='#1e1e1e', 
            fg='#ff9e64', 
            height=10
        )
        self.vision_display.grid(row=2, column=0, sticky="nsew", pady=(5,0))

        # Actions display (remains unchanged)
        ttk.Label(display_frame, text="Actions:").grid(row=0, column=1, sticky="w", padx=5)
        self.actions_display = scrolledtext.ScrolledText(
            display_frame, 
            wrap=tk.WORD, 
            bg='#1e1e1e', 
            fg='#ffffff', 
            height=20
        )
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
        
        # Add cancel button next to send button
        self.cancel_button = ttk.Button(
            input_frame, 
            text="Cancel", 
            command=self.cancel_operation,
            state="disabled"
        )
        self.cancel_button.grid(row=0, column=2, padx=5)
        
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
        
        # Add service initialization
        self.groq_service = GroqService()
        self.screenshot_service = ScreenshotService()
        self.action_executor = ActionExecutor()
        self.is_executing = False
        
        # Create event loop
        self.loop = asyncio.get_event_loop()
        
        # Start update loop and connection check using after method
        self.root.after(100, self.check_connection)
        self.root.after(50, self.start_update_loop)
        
        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        
        # Add retry settings
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Add cancel flag
        self.is_cancelled = False
        
        # Add history manager
        self.history_manager = HistoryManager()
    
    def cleanup(self) -> None:
        """Clean up resources before closing."""
        self.history_manager.clear()
        self.loading_animation.stop()
        self.thread_pool.shutdown(wait=False)
        self.root.destroy()
    
    def check_connection(self) -> None:
        """Check Ollama server connection status with retry."""
        try:
            self.client.list()
            if not self.is_connected:
                self.status_label.config(text="🟢 Connected")
                self.is_connected = True
        except Exception as e:
            self.status_label.config(text="⚫ Disconnected")
            self.is_connected = False
            self.queue_update('error', f"Connection error: {str(e)}\n")
        finally:
            self.root.after(5000, self.check_connection)
    
    def send_message(self, event=None) -> None:
        """Handle message sending with debouncing."""
        current_time = time.time()
        if current_time - self.last_input_time < 0.1:  # 100ms debouncing
            return
        
        user_input = self.input_field.get().strip()
        if not user_input:
            return
        
        self.history_manager.set_objective(user_input)  # Store objective
        
        self.last_input_time = current_time
        self.input_field.delete(0, tk.END)
        self.actions_display.insert(tk.END, f"You: {user_input}\n\n")
        self.actions_display.see(tk.END)
        
        if not self.is_connected:
            self.actions_display.insert(tk.END, "Error: Not connected to Ollama server\n\n")
            return
        
        self.is_cancelled = False
        self.cancel_button.configure(state="normal")
        self.loading_animation.start()
        self.send_button.configure(state="disabled")
        self.loop.create_task(self.process_input(user_input))
    
    def toggle_interface(self) -> None:
        """Toggle interface based on model selection."""
        if self.model_type_var.get() == "groq":
            self.thoughts_display.grid_remove()
            self.actions_display.configure(height=30)  # Make actions panel taller
        else:
            self.thoughts_display.grid()
            self.actions_display.configure(height=20)
    
    async def process_input(self, user_input: str) -> None:
        retries = 0
        self.is_executing = True
        
        while retries < self.max_retries and not self.is_cancelled and self.is_executing:
            try:
                # Take screenshot and analyze
                screenshot = self.screenshot_service.capture_and_encode()
                vision_context = TextUtils.read_context("context.txt")
                
                # Get vision analysis
                vision_response = await self.get_vision_analysis(screenshot, vision_context)
                self.vision_display.insert(tk.END, f"Vision Analysis:\n{vision_response}\n\n")
                self.vision_display.see(tk.END)
                
                # Generate and execute command
                command_response = await self.generate_command(
                    user_input,
                    vision_response,
                    self.history_manager.format_history()
                )
                
                if command_response:
                    # Parse and execute command
                    reason, action = self.action_executor.parse_yaml_response(command_response)
                    
                    # Display reason and action
                    self.queue_update('action', f"Reason: {reason}\nExecuting: {action}\n")
                    
                    if action.lower() == 'done':
                        self.is_executing = False
                        self.queue_update('action', "Task completed.\n\n")
                        break
                    
                    # Execute command and wait
                    success = self.action_executor.execute_command(action)
                    self.history_manager.add_command(reason, action, success)
                    
                    if success:
                        await asyncio.sleep(3)  # Wait for UI update
                        continue
                    
                break  # Exit if command execution fails
                
            except Exception as e:
                if self.is_cancelled:
                    break
                self.queue_update('error', f"Error: {str(e)}\n\n")
                retries += 1
                if retries >= self.max_retries:
                    break
                await asyncio.sleep(self.retry_delay)
        
        self.is_executing = False
        self.root.after(0, self._reset_ui_state)
    
    async def get_vision_analysis(self, screenshot: str, context: str) -> str:
        """Get vision analysis with timeout."""
        vision_future = self.loop.run_in_executor(
            None,
            partial(self.groq_service.analyze_image, screenshot, context)
        )
        return await asyncio.wait_for(vision_future, timeout=30)
    
    async def generate_command(self, user_input: str, vision_response: str, history: str) -> Optional[str]:
        """Generate next command based on vision analysis and history."""
        context2 = TextUtils.read_context("context2.txt")
        combined_prompt = (
            f"{context2}\n\n"
            f"Task Objective: {user_input}\n\n"
            f"Command History:\n{history}\n\n"
            f"Current Vision Analysis:\n{vision_response}\n\n"
            f"Based on the history above and current vision analysis, "
            f"determine the next action to progress towards the objective. "
            f"Ensure you don't repeat previous actions unless necessary."
        )
        
        if self.model_type_var.get() == "groq":
            command_future = self.loop.run_in_executor(
                None,
                partial(self.groq_service.generate_command, combined_prompt)
            )
            return await asyncio.wait_for(command_future, timeout=30)
        else:
            return await self.loop.run_in_executor(None, self.get_response, combined_prompt)
    
    def get_response(self, prompt: str) -> None:
        try:
            model = self.model_var.get()
            current_thought = []
            in_thought = False
            
            for chunk in self.client.generate(model=model, prompt=prompt, stream=True):
                if self.is_cancelled:
                    return
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
            if not self.is_cancelled:
                self.queue_update('error', f"Error: {str(e)}\n\n")
        finally:
            self.root.after(0, self._reset_ui_state)
    
    def _reset_ui_state(self) -> None:
        """Reset UI elements after processing."""
        self.loading_animation.stop()
        self.send_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.is_cancelled = False
    
    def cancel_operation(self) -> None:
        """Cancel ongoing operations."""
        self.is_cancelled = True
        self.queue_update('error', "Operation cancelled by user\n\n")
        self._reset_ui_state()
    
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

def main():
    root = tk.Tk()
    root.title("AI Assistant")
    
    # Configure asyncio loop to work with tkinter
    if sys.platform.startswith('win'):
        # Windows specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.get_event_loop()
    
    app = OllamaGUI(root)
    
    # Function to periodically update asyncio loop
    def update_async_loop():
        loop.stop()
        loop.run_forever()
        root.after(100, update_async_loop)
    
    # Start the async loop update
    root.after(100, update_async_loop)
    
    try:
        root.mainloop()
    finally:
        loop.close()

if __name__ == "__main__":
    main()
