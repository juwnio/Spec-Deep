import tkinter as tk
from tkinter import scrolledtext
import requests
import json
import re
import pyautogui
import base64
import os
import time
import ast
import win32gui
import win32con
import threading
import itertools

class WindowFocusManager:
    def __init__(self):
        self.last_active_window = None
    
    def store_current_focus(self):
        self.last_active_window = win32gui.GetForegroundWindow()
    
    def restore_focus(self):
        if self.last_active_window:
            # Activate the last active window
            win32gui.ShowWindow(self.last_active_window, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(self.last_active_window)

class VisionProcessor:
    def __init__(self, api_key, base_url, root_window, focus_manager):
        self.api_key = api_key
        self.base_url = base_url
        self.root_window = root_window
        self.focus_manager = focus_manager

    def capture_and_encode_screenshot(self):
        # Store current window state and focus
        current_state = self.root_window.state()
        self.focus_manager.store_current_focus()
        
        # Minimize window
        self.root_window.iconify()
        
        # Small delay to ensure window is minimized
        time.sleep(0.5)
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Restore window to previous state
        if current_state == 'zoomed':
            self.root_window.state('zoomed')
        else:
            self.root_window.deiconify()
            
        # Restore previous window focus
        time.sleep(0.1)  # Small delay to ensure window states are settled
        self.focus_manager.restore_focus()
            
        screenshot.save("temp_screenshot.png")
        with open("temp_screenshot.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        os.remove("temp_screenshot.png")
        return encoded_string

    def analyze_image(self, base64_image):
        with open("context.txt", "r") as f:
            vision_context = f.read()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.2-90b-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_context},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

class AutomationState:
    def __init__(self):
        self.command_history = []
        self.last_vision_response = None
        self.last_command_executed = None
        self.task_completed = False
        self.error_count = 0
        self.max_retries = 3
        self.current_task = None

    def add_command_to_history(self, command):
        self.command_history.append({
            'command': command,
            'timestamp': time.strftime('%H:%M:%S')
        })

class CommandProcessor:
    def __init__(self):
        self.valid_commands = ['press', 'typewrite', 'click', 'doubleClick', 'rightClick', 
                             'moveTo', 'hotkey', 'scroll', 'dragTo']
    
    def extract_commands(self, response_text):
        commands = []
        pattern = r'action:\s*pyautogui\.([^(\n]*\([^)]*\))'
        matches = re.finditer(pattern, response_text)
        
        for match in matches:
            cmd = match.group(1)
            if any(valid_cmd in cmd for valid_cmd in self.valid_commands):
                commands.append(cmd)
        return commands
    
    def execute_command(self, command):
        try:
            cmd_parts = command.split('(', 1)
            func_name = cmd_parts[0].strip()
            args_str = '(' + cmd_parts[1]
            args = ast.literal_eval(args_str)
            
            func = getattr(pyautogui, func_name)
            
            if isinstance(args, tuple):
                func(*args)
            else:
                func(args)
            return True
        except Exception as e:
            print(f"Command execution error: {e}")
            return False

class LoadingAnimation:
    def __init__(self, label):
        self.label = label
        self.running = False
        self.chars = itertools.cycle(['|', '/', '-', '\\'])
        
    def start(self):
        self.running = True
        self.animate()
        
    def stop(self):
        self.running = False
        self.label.config(text="")
        
    def animate(self):
        if self.running:
            self.label.config(text=next(self.chars))
            self.label.after(100, self.animate)

class DarkTheme:
    BG_DARK = "#1e1e1e"
    BG_DARKER = "#252526"
    FG_LIGHT = "#d4d4d4"
    ACCENT = "#007acc"
    INPUT_BG = "#3c3c3c"
    
    @classmethod
    def configure(cls, widget):
        if isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
            widget.configure(
                bg=cls.INPUT_BG,
                fg=cls.FG_LIGHT,
                insertbackground=cls.FG_LIGHT,
                selectbackground=cls.ACCENT,
                relief=tk.FLAT,
                padx=10,
                pady=5
            )
        elif isinstance(widget, tk.Button):
            widget.configure(
                bg=cls.ACCENT,
                fg=cls.FG_LIGHT,
                activebackground=cls.BG_DARKER,
                activeforeground=cls.FG_LIGHT,
                relief=tk.FLAT,
                padx=20
            )
        elif isinstance(widget, tk.Label):
            widget.configure(
                bg=cls.BG_DARK,
                fg=cls.FG_LIGHT
            )
        elif isinstance(widget, tk.Frame):
            widget.configure(
                bg=cls.BG_DARK
            )

class GroqInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Automation")
        self.root.configure(bg=DarkTheme.BG_DARK)
        
        # Initialize components
        self.focus_manager = WindowFocusManager()
        self.api_key = "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"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.vision_processor = VisionProcessor(self.api_key, self.base_url, self.root, self.focus_manager)
        self.command_processor = CommandProcessor()
        self.automation_state = AutomationState()
        
        self.create_widgets()

    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        DarkTheme.configure(main_frame)
        
        # Task input section
        task_frame = tk.Frame(main_frame)
        task_frame.pack(fill=tk.X, pady=(0, 20))
        DarkTheme.configure(task_frame)
        
        task_label = tk.Label(task_frame, text="Task:")
        task_label.pack(anchor='w', pady=(0, 5))
        DarkTheme.configure(task_label)
        
        self.input_text = tk.Text(task_frame, height=3)
        self.input_text.pack(fill=tk.X)
        DarkTheme.configure(self.input_text)
        
        button_frame = tk.Frame(task_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        DarkTheme.configure(button_frame)
        
        submit_btn = tk.Button(button_frame, text="Execute Task", command=self.process_workflow)
        submit_btn.pack(side=tk.LEFT)
        DarkTheme.configure(submit_btn)
        
        # Loading animation
        self.loading_label = tk.Label(button_frame, text="", width=2)
        self.loading_label.pack(side=tk.LEFT, padx=10)
        DarkTheme.configure(self.loading_label)
        self.loading_animation = LoadingAnimation(self.loading_label)
        
        # Status section
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.BOTH, expand=True)
        DarkTheme.configure(status_frame)
        
        # Reason panel
        reason_label = tk.Label(status_frame, text="Reason for Action:")
        reason_label.pack(anchor='w', pady=(0, 5))
        DarkTheme.configure(reason_label)
        
        self.reason_text = scrolledtext.ScrolledText(status_frame, height=3)
        self.reason_text.pack(fill=tk.X)
        DarkTheme.configure(self.reason_text)
        
        # Action panel
        action_label = tk.Label(status_frame, text="Action:")
        action_label.pack(anchor='w', pady=(10, 5))
        DarkTheme.configure(action_label)
        
        self.action_text = scrolledtext.ScrolledText(status_frame, height=3)
        self.action_text.pack(fill=tk.X)
        DarkTheme.configure(self.action_text)

    def process_workflow(self):
        self.loading_animation.start()
        threading.Thread(target=self._process_workflow_thread, daemon=True).start()

    def _process_workflow_thread(self):
        try:
            user_prompt = self.input_text.get("1.0", tk.END).strip()
            self.automation_state = AutomationState()
            self.execute_automation_loop(user_prompt)
        except Exception as e:
            self.log_error(f"Workflow error: {str(e)}")
        finally:
            self.root.after(0, self.loading_animation.stop)

    def update_status(self, reason, action):
        def _update():
            self.reason_text.delete("1.0", tk.END)
            self.reason_text.insert(tk.END, reason)
            self.action_text.delete("1.0", tk.END)
            self.action_text.insert(tk.END, action)
        self.root.after(0, _update)

    def execute_automation_loop(self, user_prompt):
        self.automation_state.current_task = user_prompt
        
        while not self.automation_state.task_completed:
            try:
                # Get vision analysis
                vision_response = self.get_vision_analysis()
                if not vision_response:
                    continue

                # Get DeepSeek response
                deepseek_response = self.get_deepseek_response(vision_response, user_prompt)
                if not deepseek_response:
                    continue

                # Check for completion
                if self.check_task_completion(deepseek_response):
                    break

                # Extract single command
                commands = self.command_processor.extract_commands(deepseek_response)
                if not commands:
                    continue

                # Execute only the first command
                cmd = commands[0]  # Take only the first command
                if self.execute_single_command(cmd):
                    self.automation_state.add_command_to_history(cmd)
                else:
                    self.automation_state.error_count += 1
                    if self.automation_state.error_count >= self.automation_state.max_retries:
                        self.log_error("Max retries reached. Stopping automation.")
                        break

                # Wait before next iteration
                time.sleep(3)
                self.root.update()

            except Exception as e:
                self.log_error(f"Loop iteration error: {str(e)}")
                self.automation_state.error_count += 1
                if self.automation_state.error_count >= self.automation_state.max_retries:
                    break

    def get_vision_analysis(self):
        try:
            base64_image = self.vision_processor.capture_and_encode_screenshot()
            vision_response = self.vision_processor.analyze_image(base64_image)
            self.automation_state.last_vision_response = vision_response
            return vision_response
        except Exception as e:
            self.log_error(f"Vision analysis error: {str(e)}")
            return None

    def get_deepseek_response(self, vision_response, user_prompt):
        try:
            with open("context2.txt", "r") as f:
                final_context = f.read()
            
            history_text = "\n".join([
                f"Previously executed: {h['command']} at {h['timestamp']}"
                for h in self.automation_state.command_history
            ])
            
            combined_prompt = (
                f"{final_context}\n\n"
                f"COMMAND HISTORY:\n{history_text}\n\n"
                f"UPDATE OF SCREEN:\n{vision_response}\n\n"
                f"ORIGINAL TASK: {self.automation_state.current_task}\n\n"
                f"CURRENT PROMPT: {user_prompt}"
            )
            
            return self.send_to_deepseek(combined_prompt)
        except Exception as e:
            self.log_error(f"DeepSeek response error: {str(e)}")
            return None

    def check_task_completion(self, response):
        if ("reason_for_action: Task successfully completed" in response and 
            "action: done" in response):
            self.automation_state.task_completed = True
            return True
        return False

    def execute_single_command(self, command):
        try:
            success = self.command_processor.execute_command(command)
            if success:
                self.automation_state.last_command_executed = command
                self.log_status(f"Executed: {command}")
            return success
        except Exception as e:
            self.log_error(f"Command execution error: {str(e)}")
            return False

    def log_status(self, status_message):
        print(f"Status: {status_message}")
        self.update_status("Status", status_message)
        self.root.update()

    def execute_commands(self, response):
        try:
            commands = self.command_processor.extract_commands(response)
            if not commands:
                return False
                
            for cmd in commands:
                success = self.command_processor.execute_command(cmd)
                if not success:
                    return False
                self.automation_state.last_command_executed = cmd
                self.root.update()  # Update GUI
                time.sleep(3)  # Wait between commands
            return True
        except Exception as e:
            self.log_error(f"Command execution error: {str(e)}")
            return False

    def log_error(self, error_message):
        print(f"Error: {error_message}")
        self.update_status("Error", error_message)
        self.root.update()

    def send_to_deepseek(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-r1-distill-llama-70b",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            
            # Extract reason and action
            reason_match = re.search(r'reason_for_action:\s*(.*?)\n', response_text)
            action_match = re.search(r'action:\s*(.*?)(?:\n|$)', response_text)
            
            reason = reason_match.group(1) if reason_match else ""
            action = action_match.group(1) if action_match else ""
            
            self.update_status(reason, action)
            return response_text
            
        except Exception as e:
            self.update_status("Error", str(e))
            return ""

    def parse_response(self, response_text):
        think_pattern = r'<think>(.*?)</think>'
        think_match = re.search(think_pattern, response_text, re.DOTALL)
        
        if think_match:
            think_content = think_match.group(1).strip()
            # Get everything after </think>
            action_content = re.split(r'</think>', response_text)[-1].strip()
        else:
            think_content = ""
            action_content = response_text
            
        return think_content, action_content

if __name__ == "__main__":
    root = tk.Tk()
    app = GroqInterface(root)
    root.geometry("600x400")
    root.mainloop()
